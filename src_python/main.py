import asyncio
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
    logger.debug("Main", f"Debug: {DEBUG}")
    logger.debug("Main", f"[fast] : {fast_str}")

    logger.info("Main", "Démarrage broker...")
    logger.info("Main", "Démarrage clients...")

    # return_exceptions=True : si un agent plante (bug de stratégie, etc.), on
    # ne veut pas que ça annule le broker et les autres agents en plein vol
    # (ça fermait les serveurs WebSocket en cours de route, et les clients
    # encore connectés recevaient une déconnexion 1001 sans aucune trace de
    # la vraie cause). On journalise l'erreur et la simulation continue.
    results = await asyncio.gather(
        broker(mode=mode, file=file, fast=fast_str, nb_clients=nb_clients),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
                   AI(wallet=1000, portfolio={}, nn=None, tolerance=0.01),
                   "agent1", db),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
                   AI(wallet=2000, portfolio={}, nn=None, tolerance=0.10),
                   "agent2", db),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
                   AI(wallet=500, portfolio={}, nn=None, tolerance=0.20),
                   "agent3", db),
        return_exceptions=True,
    )
    for result in results:
        if isinstance(result, Exception):
            logger.error("Main", f"Une tâche s'est terminée en erreur : {result!r}")

    logger.close()