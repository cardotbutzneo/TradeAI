import sys
import time
import random
import math
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt

def generer_flux_bourse(ticker="GOOG", prix_initial=142.05, jours=100, devise="euro"):
    """
    Simule un historique boursier via un Mouvement Brownien Géométrique.
    Envoie les données sur stdout au format CSV.
    """
    # Paramètres financiers annuels convertis en quotidiens
    drift = 0.10 / 252       # +10% de rendement attendu par an (252 jours de bourse)
    volatility = 0.25 / math.sqrt(252) # 25% de volatilité annuelle
    
    prix_actuel = prix_initial
    date_actuelle = datetime(2026, 6, 22) # Date d'aujourd'hui en 2026

    for _ in range(jours):
        # Hasard distribué selon une loi normale (Gaussienne)
        hasard = random.gauss(0, 1)
        
        # Formule mathématique du Mouvement Brownien Géométrique
        facteur_croissance = math.exp(drift + volatility * hasard)
        prix_actuel = prix_actuel * facteur_croissance
        
        # Formatage de la ligne CSV
        date_str = date_actuelle.strftime("%Y/%m/%d")
        ligne = f"{ticker},{prix_actuel:.2f},{date_str},{devise}\n"
        
        # Envoi immédiat à ton programme C
        sys.stdout.write(ligne)
        sys.stdout.flush()
        
        # On recule d'un jour (pour coller à ton format historique du haut vers le bas)
        date_actuelle -= timedelta(days=1)
        
        # Optionnel : décommente la ligne du dessous si tu veux simuler un flux temps réel (0.1s entre chaque jour)
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
    all_tiker = ["GOOG", "AMZ"]
    all_start_price = [142.05, 41.02]
    for tiker, start_price in zip(all_tiker, all_start_price):
        generer_flux_bourse(tiker, prix_initial=start_price, jours=150)
    
    graphique("historic.csv")
    
