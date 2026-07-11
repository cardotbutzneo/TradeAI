import asyncio
import sys
from AI import AI 
from train_AI import NeuralNetwork, build_dataset
from broker import broker
from run_client import run_client
from graphic import price_graph

"""Main file to run the broker and clients for the trading simulation.
- main(): Starts the broker and multiple clients in parallel, each with its own AI agent."""

PORT_ECOUTE_CLIENT = "ws://127.0.0.1:8766"
PORT_ECOUTE_SERVEUR = "ws://127.0.0.1:8765"

async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--train"
    file = sys.argv[2] if len(sys.argv) > 2 else ""
    fast_str = sys.argv[3] if len(sys.argv) > 3 else ""
    print(f"[fast] : {fast_str}", file=sys.stderr)

    # nn = NeuralNetwork([5, 16, 8, 3])
    # X, y = build_dataset("data/historic.csv")
    # nn.train(X, y, epochs=1000)
    # Lance 3 agents en parallèle sur le même serveur

    print("[Main] Démarrage broker...", file=sys.stderr)
    print("[Main] Démarrage clients...", file=sys.stderr)
    await asyncio.gather(
        broker(mode=mode, file=file, fast=fast_str, nb_clients=3),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT, AI(wallet=1000, portfolio={}, nn=None, tolerance=0.01), "agent1"),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT, AI(wallet=2000, portfolio={}, nn=None, tolerance=0.10), "agent2"),
        run_client(PORT_ECOUTE_SERVEUR, PORT_ECOUTE_CLIENT, AI(wallet=500,  portfolio={}, nn=None, tolerance=0.20), "agent3"),
    )

asyncio.run(main())