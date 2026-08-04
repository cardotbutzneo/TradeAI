import asyncio
import subprocess
import sys
import websockets
import time

from .utils.logger import logger
from .utils.utils import Return_code

"""broker.py — WebSocket broker for the trading simulation.
- handler_ticks(websocket): Handles incoming tick data from the C++ process and broadcasts it to connected clients.
- handler_ordres(websocket): Handles incoming orders from clients and forwards them to the C++ process, then sends back acknowledgments.
- broker(cpp_path, mode, fast, file, nb_clients): Starts the C++ process and sets up WebSocket servers for ticks and orders, managing client connections and communication."""

process = None
clients_ticks:   set = set() # tick sur un port précis
clients_connectes: dict[str, websockets.WebSocketServerProtocol] = {}  # id → websocket
valeur_clients : dict[str, float] = {} # sauvegarde pour plus de facilité lors de l'envoie des données
ack_queues: dict[str, asyncio.Queue] = {}  # id → queue d'ACKs
# broker.py
clients_attendus = 0  # nombre de clients attendus
clients_prets = asyncio.Event()  # signal "tous connectés"
moteur_arrete = False  # mis à True dès que lire_cpp() voit STOP (ou un crash) ;
                        # évite à handler_ordres de tenter une écriture qu'on
                        # sait déjà vouée à l'échec (cf. rapport.txt, course
                        # de fin de run). Ne supprime pas 100% des cas : le
                        # process peut mourir entre la lecture de ce flag et
                        # l'écriture, d'où le try/except qui reste en filet.

async def _broadcast(sockets, message):
    """Send `message` to every socket without letting one already-dead/closing
    connection abort the others or crash the caller. A client can disconnect
    (or its write can fail, see handler_ordres) at any point, including in the
    exact instant the C++ engine is shutting down -- a plain gather() would
    let that single failure propagate and take down the whole broker() task."""
    results = await asyncio.gather(*[ws.send(message) for ws in sockets], return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.warn("Broker", f"Envoi échoué vers un client déjà déconnecté : {result!r}")

async def handler_ticks(websocket):
    """Connexion en lecture seule pour recevoir les TICKs"""
    clients_ticks.add(websocket)
    try:
        await websocket.wait_closed()  # attend que le client se déconnecte
    finally:
        clients_ticks.discard(websocket)

async def handler_ordres(websocket):
    global clients_attendus
    init_msg = await websocket.recv()
    agent_id, solde_str = init_msg.split(";")
    solde = float(solde_str)
    logger.debug("Broker", f"{agent_id=}-{solde=}")

    clients_connectes[agent_id] = websocket
    ack_queues[agent_id] = asyncio.Queue()
    valeur_clients[agent_id] = solde

    await websocket.send(f"REGISTERED;{agent_id};OK")
    logger.info("Broker", f"{agent_id} enregistré ({len(clients_connectes)}/{clients_attendus})")

    # Signal quand tous les clients sont connectés
    if len(clients_connectes) >= clients_attendus:
        clients_prets.set()

    try:
        async for message in websocket:
            if message == "PASS":
                order_line = f"{agent_id}|PASS\n"
                nb_orders = 1
            else:
                # Format vers C++ : "agent1|BUY;GOOG;10|BUY;AMZ;5"
                order_line = f"{agent_id}|{message}\n"
                # Le C++ répond avec une ligne ACK par ordre reçu (voir
                # process_order_line côté C++) : il faut donc dépiler
                # exactement ce nombre d'ACKs avant de répondre au client,
                # sinon les ACKs en trop restent dans la queue et sont lus
                # par erreur au tour suivant (désynchronisation permanente).
                nb_orders = len([o for o in message.split("|") if o])

            if moteur_arrete:
                # On sait déjà (flag posé par lire_cpp dès "STOP"/crash lu)
                # que l'écriture échouerait : on l'évite plutôt que de
                # provoquer un BrokenPipeError pour rien. Réduit la plupart
                # des cas de la course de fin de run, mais pas 100% d'entre
                # eux : le process peut aussi mourir dans la fenêtre entre ce
                # test et l'écriture ci-dessous (cf. try/except restant).
                logger.debug("Broker", f"Ordre de {agent_id} ignoré, moteur déjà arrêté.")
                await websocket.send("|".join([f"ACK;{agent_id};REJECT_ENGINE_STOPPED"] * nb_orders))
                continue

            try:
                process.stdin.write(order_line)
                process.stdin.flush()
            except (BrokenPipeError, ValueError) as e:
                # Le moteur C++ a déjà quitté (ex: ordre arrivé juste après le
                # dernier tick, une fois "STOP" imprimé) : pas d'ACK possible,
                # on le signale proprement au client plutôt que de laisser
                # planter la connexion (ce qui cascadait en ConnectionClosedError
                # ailleurs, cf. rapport.txt).
                logger.warn("Broker", f"Écriture vers le C++ impossible pour {agent_id} (moteur arrêté) : {e!r}")
                await websocket.send("|".join([f"ACK;{agent_id};REJECT_ENGINE_STOPPED"] * nb_orders))
                continue

            acks = [await ack_queues[agent_id].get() for _ in range(nb_orders)]
            await websocket.send("|".join(acks))
    finally:
        clients_connectes.pop(agent_id, None)
        ack_queues.pop(agent_id, None)

async def broker(cpp_path="./src_cpp/main", mode="train", fast="",
                 file="", nb_clients=1):
    global process, clients_attendus, moteur_arrete
    clients_attendus = nb_clients
    moteur_arrete = False

    args = [cpp_path, mode]
    if file: args.append(file)
    args.append(fast)

    logger.info("Broker", f"{args}")

    process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, text=True)

    async with websockets.serve(handler_ticks, "127.0.0.1", 8765), \
               websockets.serve(handler_ordres, "127.0.0.1", 8766):
        logger.info("Broker", f"Attente de {nb_clients} client(s)...")

        try:
            await asyncio.wait_for(clients_prets.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.error(
                "Broker",
                "Délai d'attente dépassé : tous les clients ne se sont pas connectés.",
            )
            exit(Return_code.TIMEOUT)

        if len(clients_connectes) > 0:
            logger.info("Broker", "Déclaration des clients au C++...")
            fmt_str = "|".join(
                [f"{c_id}:{solde}" for c_id, solde in valeur_clients.items()]
            )
            process.stdin.write(f"REGISTER;{fmt_str}\n")
            process.stdin.flush()
        else:
            logger.error("Broker", "Aucun client connecté. Arret du programme...")
            return
        
        await clients_prets.wait()
        logger.debug("Broker", f"Tous les clients connectés, démarrage...")

        logger.debug("Broker", "Envoi START au C++")

        logger.debug("Broker", f"process: {process.pid}")
        process.stdin.write("START\n")
        process.stdin.flush()
        await lire_cpp()

    try:
        # close() flushes any buffered bytes first; if the C++ process already
        # exited (the normal case right after "STOP"), that flush can itself
        # raise BrokenPipeError -- same race as the writes in handler_ordres,
        # just one step later. lire_cpp() only returns once moteur_arrete is
        # True, so reaching this point with a dead process is the expected
        # outcome of every normal run, not a warning-worthy event.
        process.stdin.close()
    except (BrokenPipeError, OSError) as e:
        logger.debug("Broker", f"Fermeture du stdin C++ (déjà terminé) : {e!r}")
    process.wait()

async def lire_cpp():
    """Lit stdout du C++ et trie TICKs et ACKs"""
    global moteur_arrete
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, process.stdout.readline)
        line = line.strip()
        logger.debug("Broker", f"reçu C++ : '{line}'")

        if not line:
            # Flux stdout fermé sans ligne "STOP" explicite : le process C++
            # est mort prématurément (crash) plutôt que d'avoir terminé
            # normalement. On le journalise pour ne pas confondre ça avec
            # un arrêt propre la prochaine fois que ça arrive.
            exit_code = process.poll()
            logger.error("Broker", f"Flux C++ interrompu sans STOP (code retour : {exit_code}).")
            moteur_arrete = True  # posé avant le broadcast (cf. définition du flag plus haut)
            await _broadcast(list(clients_connectes.values()), "STOP")
            break

        if line == "STOP":
            moteur_arrete = True  # posé avant le broadcast (cf. définition du flag plus haut)
            await _broadcast(list(clients_connectes.values()), "STOP")
            break

        elif line.startswith("TICK;"):
            # Broadcast à tous les clients
            if clients_ticks:
                await _broadcast(list(clients_ticks), line)

        elif line.startswith("ACK;"):
            # Format attendu : "ACK;agent1;OK;9713|ACK;agent2;REJECT_NO_CASH"
            for sub_ack in line.split("|"):
                if not sub_ack: continue
                parts = sub_ack.split(";")
                if len(parts) < 3: continue
                target_id = parts[1]  # "agent1"
                if target_id in ack_queues:
                    await ack_queues[target_id].put(sub_ack)
                else:
                    logger.info("Broker", f"ACK pour client inconnu : {target_id}")

        elif line.startswith("REGISTER;"):
            if clients_ticks:
                await _broadcast(list(clients_ticks), line)