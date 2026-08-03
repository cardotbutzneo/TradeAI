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
    logger.debug("Main", f"Debug: {DEBUG}")
    logger.debug("Main", f"[fast] : {fast_str}")

    logger.info("Main", "Démarrage broker...")
    logger.info("Main", "Démarrage clients...")

    await asyncio.gather(
        broker(mode=mode, file=file, fast=fast_str, nb_clients=nb_clients),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
                   AI(wallet=1000, portfolio={}, nn=None, tolerance=0.05, strategy="mean_reversion"),
                   "agent1", db),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
                   AI(wallet=1000, portfolio={}, nn=None, tolerance=0.10, strategy="momentum"),
                   "agent2", db),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT,
                   AI(wallet=1000, portfolio={}, nn=None, tolerance=0.15, strategy="rsi_contrarian"),
                   "agent3", db),
    )

    logger.close()