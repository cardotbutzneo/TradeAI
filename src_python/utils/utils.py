import json
import sys
from enum import Enum

class Return_code(Enum):
    SUCCESS = 0
    CONFIG_ERROR = 3
    PORT_BIND_FAILED = 4
    ENGINE_CRASH = 5
    INVALIDE_ARG = 6
    FAIL_CONNECTION = 7
    TIMEOUT = 255

# Flat tax française (PFU) sur les plus-values de cession, appliquée uniquement
# à la vente. Codée en dur (n'a pas vocation à bouger souvent), contrairement
# aux frais de courtage ci-dessous qui sont configurables via settings.json.
# Miroir de FLAT_TAX_RATE dans src_cpp/include/header.h -- source de vérité
# unique côté Python, le C++ reçoit les taux effectifs via CLI (voir broker.py).
FLAT_TAX_RATE = 0.302

_DEFAULT_BROKER_BUY_FEE = 0.001
_DEFAULT_BROKER_SELL_FEE = 0.008

def get_settings():
    try:
        with open("config/settings.json", 'r') as file:
            data = json.load(file)

            # json.load convertit déjà 'true'/'false' en booléens Python,
            # mais bool() ne fait pas de mal pour sécuriser.
            debug = bool(data.get("debug-mode", False))
            output_file = data.get("output-file", "output/stdout.log")
            error_file = data.get("error-file", "output/stderr.log")
            fees = data.get("broker-fees", {})
            broker_buy_fee = float(fees.get("buy", _DEFAULT_BROKER_BUY_FEE))
            broker_sell_fee = float(fees.get("sell", _DEFAULT_BROKER_SELL_FEE))

    except FileNotFoundError as e:
        print(f"[MAIN-PYTHON]: Fichier introuvable ({e}), utilisation des valeurs par défaut.")
        debug = False
        output_file = "output/stdout.log"
        error_file = "output/stderr.log"
        broker_buy_fee = _DEFAULT_BROKER_BUY_FEE
        broker_sell_fee = _DEFAULT_BROKER_SELL_FEE
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        print(f"[MAIN-PYTHON]: Erreur dans le fichier JSON ({e}), valeurs par défaut.")
        debug = False
        output_file = "output/stdout.log"
        error_file = "output/stderr.log"
        broker_buy_fee = _DEFAULT_BROKER_BUY_FEE
        broker_sell_fee = _DEFAULT_BROKER_SELL_FEE

    # On retourne les paramètres sous forme de dictionnaire (ou de tuple)
    return {
        "DEBUG": debug,
        "OUTPUT_FILE": output_file,
        "ERROR_FILE": error_file,
        "BROKER_BUY_FEE": broker_buy_fee,
        "BROKER_SELL_FEE": broker_sell_fee,
    }

config = get_settings()

DEBUG, OUTPUT_FILE, ERROR_FILE = config["DEBUG"], config["OUTPUT_FILE"], config["ERROR_FILE"]
BROKER_BUY_FEE, BROKER_SELL_FEE = config["BROKER_BUY_FEE"], config["BROKER_SELL_FEE"]
# Taux effectifs vus par les agents pour leurs décisions (voir AI.py) : le BUY
# ne supporte que le frais de courtage, le SELL supporte en plus la flat tax.
BUY_FEE_RATE = BROKER_BUY_FEE
SELL_FEE_RATE = FLAT_TAX_RATE + BROKER_SELL_FEE