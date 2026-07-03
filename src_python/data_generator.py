import sys
import time
import random
import math
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import hashlib

def generer_flux_bourse(ticker="GOOG", prix_initial=142.05, jours=5, devise="euro"):
    """
    Simule un historique boursier via un Mouvement Brownien Géométrique.
    Envoie les données sur stdout au format CSV.
    """
    # Paramètres financiers annuels convertis en quotidiens
    drift = 0.10 / 252       # +10% de rendement attendu par an (252 jours de bourse)
    volatility = 0.25 / math.sqrt(252) # 25% de volatilité annuelle
    
    prix_actuel = prix_initial
    date_actuelle = datetime(2026, 6, 22, 9) # ouverture à 9h00
    intervale = timedelta(minutes=5)

    points_par_jour = 102 # génère 102 pts par jour soit toutes les 5 minutes

    for j in range(jours):
        for p in range(points_par_jour):
            if date_actuelle.hour >= 17 and date_actuelle.minute >= 30:
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
            
        date_actuelle += timedelta(hours=15, minutes=30) # reviens à 9h le jour d'apres
            # time.sleep(0.1)

def graphique(filename, tikers):
    """
    Affiche un graphique des prix à partir d'un fichier CSV.
    """
    dates = []
    prix = []
    
    with open(filename, 'r') as f:
        for line in f:
            temp = []
            parts = line.strip().split(',')
            if len(parts) >= 2:
                #if True :
                dates.append(parts[2])  # Date
                temp.append(float(parts[1]))  # Prix
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prix, marker='o')
    plt.title(f"Historique des prix")
    #plt.xlabel("Date")
    plt.ylabel("Prix")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Génère 150 jours de cotation pour Google
    all_tiker = ["GOOG", "APPL"]
    all_start_price = [142.05, 41.02]
    for tiker, start_price in zip(all_tiker, all_start_price):
        generer_flux_bourse(tiker, prix_initial=start_price, jours=7)
    
