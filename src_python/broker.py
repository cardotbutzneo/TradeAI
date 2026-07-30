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
                process.stdin.write(f"{agent_id}|PASS\n")
            else:
                # Format vers C++ : "agent1|BUY;GOOG;10|BUY;AMZ;5"
                process.stdin.write(f"{agent_id}|{message}\n")
            process.stdin.flush()

            # Attend l'ACK du C++ pour ce client
            ack = await ack_queues[agent_id].get()
            await websocket.send(ack)
    finally:
        clients_connectes.pop(agent_id, None)
        ack_queues.pop(agent_id, None)

async def broker(cpp_path="./src_cpp/main", mode="train", fast="",
                 file="", nb_clients=1):
    global process, clients_attendus
    clients_attendus = nb_clients

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

    process.stdin.close()
    process.wait()

async def lire_cpp():
    """Lit stdout du C++ et trie TICKs et ACKs"""
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, process.stdout.readline)
        line = line.strip()
        logger.debug("Broker", f"reçu C++ : '{line}'")

        if not line or line == "STOP":
            # Prévient tous les clients
            await asyncio.gather(*[ws.send("STOP")
                                   for ws in clients_connectes.values()])
            break

        elif line.startswith("TICK;"):
            # Broadcast à tous les clients
            if clients_ticks:
                await asyncio.gather(*[ws.send(line)
                                       for ws in clients_ticks])

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
                await asyncio.gather(*[ws.send(line) for ws in clients_ticks])