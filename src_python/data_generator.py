import sys
import random
import math
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import hashlib
import argparse

"""data_generator.py — Simulates stock market data using Geometric Brownian Motion.
- valider_date(chaine_date): Validates and converts a date string to a datetime object
- parser_arguments(): Parses command-line arguments for start date and duration
- generer_flux_bourse(date_actuelle, ticker, prix_initial, jours, devise): Generates stock market data for a given ticker and writes it to stdout in CSV format"""

def valider_date(chaine_date):
    try:
        return datetime.strptime(chaine_date, "%Y-%m-%d").replace(hour=9, minute=30)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Format invalide : '{chaine_date}'. Utilisez AAAA-MM-JJ.")

def parser_arguments():
    args = {}
    i = 1
    while i < len(sys.argv):
        if i + 1 < len(sys.argv):
            args[sys.argv[i]] = sys.argv[i+1]
            i += 2
        else:
            i += 1

    # fdate
    if "fdate" in args:
        try:
            fdate = datetime.strptime(args["fdate"], "%Y-%m-%d").replace(hour=9, minute=30)
        except ValueError:
            print(f"Format de date invalide : '{args['fdate']}'", file=sys.stderr)
            exit(1)
    else:
        fdate = datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)

    # dur
    if "dur" in args:
        try:
            duration = int(args["dur"])
        except ValueError:
            print(f"Durée invalide : '{args['dur']}'", file=sys.stderr)
            exit(1)
    else:
        duration = 7

    return fdate, duration

def generer_flux_bourse(date_actuelle, ticker="GOOG", prix_initial=142.05, jours=7, devise="euro"):
    """
    Simule un historique boursier via un Mouvement Brownien Géométrique.
    Envoie les données sur stdout au format CSV.
    """
    # Paramètres financiers annuels convertis en quotidiens
    drift = 0.10 / 252       # +10% de rendement attendu par an (252 jours de bourse)
    volatility = 0.25 / math.sqrt(252) # 25% de volatilité annuelle
    
    prix_actuel = prix_initial
    intervale = timedelta(minutes=5)

    points_par_jour = 102 # génère 102 pts par jour soit toutes les 5 minutes

    for j in range(jours):
        for p in range(points_par_jour):
            if date_actuelle.hour > 17 or (date_actuelle.hour == 17 and date_actuelle.minute >= 0):
                break # fin de la journée  
            # Hasard distribué selon une loi normale (Gaussienne)
            hasard = random.gauss(0, 1)
            
            # Formule mathématique du Mouvement Brownien Géométrique
            facteur_croissance = math.exp(drift + volatility * hasard)
            prix_actuel = prix_actuel * facteur_croissance
            
            # Formatage de la ligne CSV
            date_str = date_actuelle.strftime("%Y/%m/%d-%H:%M:%S")
            volume = int(2000 // prix_actuel) # simule un volume de 2000€ d'actions
            hash_input       = date_str + str(volume) + ticker
            hash_transaction = hashlib.md5(hash_input.encode()).hexdigest()
            ligne = f"{date_str},{ticker},{prix_actuel:.2f},{volume},{devise},{hash_transaction}\n"
        
            sys.stdout.write(ligne)
            sys.stdout.flush()
            
            date_actuelle += intervale
            
        date_actuelle = date_actuelle.replace(hour=9, minute=30, second=0)
        date_actuelle += timedelta(days=1) # reviens à 9h le jour d'apres
            # time.sleep(0.1)

if __name__ == "__main__":
    fdate, duration = parser_arguments()

    if duration <= 0:
        print("Fatal Error : Duration can't be negative or null", file=sys.stderr)
        exit(1)

    all_ticker      = ["GOOG", "APPL"]
    all_start_price = [142.05, 41.02]

    for ticker, start_price in zip(all_ticker, all_start_price):
        generer_flux_bourse(
            date_actuelle=fdate,
            ticker=ticker,
            prix_initial=start_price,
            jours=duration
        )