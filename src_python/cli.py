import argparse
import asyncio
from .main import main as app_main


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="TradeAI orchestrator for broker and clients."
    )
    parser.add_argument(
        "mode",
        choices=["train", "prod"],
        help="Mode d'exécution : train pour utiliser un fichier historique, prod pour flux stdin.",
    )
    parser.add_argument(
        "data_file",
        nargs="?",
        default="",
        help="Chemin vers le fichier de données historique (nécessaire pour train).",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Exécute le moteur C++ en mode rapide sans pauses entre les ticks.",
    )
    parser.add_argument(
        "--clients",
        type=int,
        default=3,
        help="Nombre de clients agents à lancer en parallèle.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    fast_flag = "--fast" if args.fast else ""
    asyncio.run(app_main(mode=args.mode, file=args.data_file, fast_str=fast_flag, nb_clients=args.clients))


if __name__ == "__main__":
    main()
