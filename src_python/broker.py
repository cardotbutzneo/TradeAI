import asyncio
import subprocess
import sys
import websockets

"""broker.py — WebSocket broker for the trading simulation.
- handler_ticks(websocket): Handles incoming tick data from the C++ process and broadcasts it to connected clients.
- handler_ordres(websocket): Handles incoming orders from clients and forwards them to the C++ process, then sends back acknowledgments.
- broker(cpp_path, mode, fast, file, nb_clients): Starts the C++ process and sets up WebSocket servers for ticks and orders, managing client connections and communication."""

process = None
clients_ticks:   set = set() # tick sur un port précis
clients_connectes: dict[str, websockets.WebSocketServerProtocol] = {}  # id → websocket
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
    agent_id = await websocket.recv()
    clients_connectes[agent_id] = websocket
    ack_queues[agent_id] = asyncio.Queue()

    await websocket.send(f"REGISTERED;{agent_id}")
    print(f"[Broker] {agent_id} enregistré ({len(clients_connectes)}/{clients_attendus})", file=sys.stderr)

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

async def broker(cpp_path="./src_cpp/main", mode="--train", fast=False,
                 file="", nb_clients=1):
    global process, clients_attendus
    clients_attendus = nb_clients

    args = [cpp_path, mode]
    if file: args.append(file)

    process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, text=True)

    async with websockets.serve(handler_ordres, "127.0.0.1", 8765), \
               websockets.serve(handler_ordres, "127.0.0.1", 8766):
        print(f"[Broker] Attente de {nb_clients} client(s)...", file=sys.stderr)
        await clients_prets.wait()
        print(f"[Broker] Tous les clients connectés, démarrage...", file=sys.stderr)
        await clients_prets.wait()
        print("[Broker] Envoi START au C++", file=sys.stderr)
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
        print(f"[Broker] reçu C++ : '{line}'", file=sys.stderr)

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
                    print(f"[Broker] ACK pour client inconnu : {target_id}", file=sys.stderr)