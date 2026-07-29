import json
import sys

class Return_code:
    def __init__(self):
        _SUCCESS = 0,
        _CONFIG_ERROR = 3,
        _PORT_BIND_FAILED = 4,
        _ENGINE_CRASH = 5

def get_settings():
    try:
        with open("config/settings.json", 'r') as file:
            data = json.load(file)
            
            # json.load convertit déjà 'true'/'false' en booléens Python,
            # mais bool() ne fait pas de mal pour sécuriser.
            debug = bool(data.get("debug-mode", False))
            output_file = data.get("output-file", "output/stdout.log")
            error_file = data.get("error-file", "output/stderr.log")
            
    except FileNotFoundError as e:
        print(f"[MAIN-PYTHON]: Fichier introuvable ({e}), utilisation des valeurs par défaut.")
        debug = False
        output_file = "output/stdout.log"
        error_file = "output/stderr.log"
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[MAIN-PYTHON]: Erreur dans le fichier JSON ({e}), valeurs par défaut.")
        debug = False
        output_file = "output/stdout.log"
        error_file = "output/stderr.log"

    # On retourne les paramètres sous forme de dictionnaire (ou de tuple)
    return {
        "DEBUG": debug,
        "OUTPUT_FILE": output_file,
        "ERROR_FILE": error_file
    }

config = get_settings()

DEBUG, OUTPUT_FILE, ERROR_FILE = config["DEBUG"], config["OUTPUT_FILE"], config["ERROR_FILE"]