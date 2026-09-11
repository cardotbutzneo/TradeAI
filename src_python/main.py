import asyncio
import numpy as np
from .AI import AI
from .broker import broker
from .run_client import run_client
from .graphic import price_graph
from .utils.utils import DEBUG
from .utils.logger import logger
from .dataBase import Database 

"""Main file to run the broker and clients for the trading simulation.
- main(): Starts the broker and multiple clients in parallel, each with its own AI agent."""

PORT_ECOUTE_CLIENT = "ws://127.0.0.1:8766"
PORT_ECOUTE_SERVEUR = "ws://127.0.0.1:8765"

db = Database()

async def main(mode: str = "train",
               file: str = "",
               fast_str: str = "",
               nb_clients: int = 3):
    logger.reset()
    # db.reset() existait déjà mais n'était jamais appelé : sans ça, agents/
    # trades/ticks du run précédent restaient en base (ex: agents.finished_wallet
    # non-NULL dès le démarrage) et le dashboard affichait un mélange de
    # plusieurs runs au lieu du run en cours.
    db.reset()
    logger.debug(__file__, __name__, f"Debug: {DEBUG}")
    logger.debug(__file__, __name__, f"[fast] : {fast_str}")

    logger.info(__file__, __name__, "Démarrage broker...")
    logger.info(__file__, __name__, "Démarrage clients...")

    # return_exceptions=True : si un agent plante (bug de stratégie, etc.), on
    # ne veut pas que ça annule le broker et les autres agents en plein vol
    # (ça fermait les serveurs WebSocket en cours de route, et les clients
    # encore connectés recevaient une déconnexion 1001 sans aucune trace de
    # la vraie cause). On journalise l'erreur et la simulation continue.
    TOLERANCE_MIN, TOLERANCE_MAX = 0.05, 0.20
    tolerance_list = np.linspace(TOLERANCE_MIN, TOLERANCE_MAX, nb_clients) #génère un np.array avec une répartition linéaire de tolérance entre TOLERANCE_MIN et TOLERANCE_MAX
    # "neural_net" est exclu : cet agent est créé avec nn=None, donc cette
    # stratégie ne ferait jamais rien (strat() renvoie None sans réseau).
    strategies = ["mean_reversion", "momentum", "rsi_contrarian"]

    client_tasks = [
        run_client(
            PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
            AI(wallet=1000, portfolio={}, nn=None,
               tolerance=float(tolerance_list[i]),
               strategy=strategies[i % len(strategies)]),
            f"agent{i + 1}", db,  # id unique par client : le broker indexe
                                   # clients_connectes/ack_queues par agent_id,
                                   # un id dupliqué écraserait les entrées.
        )
        for i in range(nb_clients)
    ]

    results = await asyncio.gather(
        broker(mode=mode, file=file, fast=fast_str, nb_clients=nb_clients),
        *client_tasks,
        return_exceptions=True,
    )
    for result in results:
        if isinstance(result, Exception):
            logger.error(__file__, __name__, f"Une tâche s'est terminée en erreur : {result!r}")

    logger.close()