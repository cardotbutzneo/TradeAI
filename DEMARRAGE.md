# 🚀 Guide de démarrage (de A à Z)

Ce guide explique **pas à pas** comment lancer TradeAI, en partant de zéro.
Chaque commande est expliquée : tu sais ce qu'elle fait *avant* de l'exécuter.

> **Résumé en 1 phrase :** le projet est fait pour **Linux**. Sous Windows, on
> passe par **WSL** (un Linux intégré à Windows), on installe les outils, puis on
> lance tout avec le script `run.sh`.

---

## 1. Pourquoi WSL et pas Windows directement ?

Le projet mélange deux mondes :

- Un **moteur C++** qu'il faut **compiler** avec `g++` + `make` (outils Linux).
- Un **script d'orchestration `run.sh`** écrit en **Bash** (le shell de Linux).

PowerShell / l'invite Windows ne savent pas exécuter tout ça nativement.
**WSL** (Windows Subsystem for Linux) fournit un vrai Linux dans Windows : c'est
le plus simple. Tout ce guide se fait **dans un terminal WSL**.

> Ouvrir WSL : touche Windows → tape **« Ubuntu »** ou **« wsl »** → Entrée.
> Tu dois voir une invite qui ressemble à :
> `simonhamelin@PC2SIMON:/mnt/c/...$`

---

## 2. Installer les outils (à faire **une seule fois**)

```bash
# Met à jour la liste des paquets, puis installe :
#  - build-essential : le compilateur C++ (g++) et make
#  - python3-pip     : pip, pour installer les paquets Python
sudo apt update && sudo apt install -y build-essential python3-pip
```

`sudo` demande ton **mot de passe WSL** (celui choisi à l'installation d'Ubuntu).
Le mot de passe ne s'affiche pas quand tu le tapes, c'est normal.

Vérifie que tout est là :

```bash
g++ --version && make --version && python3 --version
```

Tu dois voir trois numéros de version, sans erreur.

---

## 3. Aller dans le dossier du projet

Le projet est sur ton disque Windows, accessible dans WSL via `/mnt/c/...` :

```bash
cd /mnt/c/Users/X515/Documents/GitHub/TradeAI
```

> `cd` = *change directory* (se déplacer dans un dossier).

---

## 4. Installer les dépendances Python (à faire **une seule fois**)

```bash
# Installe numpy, matplotlib et websockets listés dans requirements.txt.
# --break-system-packages : contourne le blocage "externally-managed" d'Ubuntu.
pip install --break-system-packages -r requirements.txt
```

> `requirements.txt` liste les 3 paquets nécessaires. Le reste (asyncio, math…)
> est déjà inclus dans Python.

---

## 5. Générer des données de marché

Le moteur a besoin d'un fichier CSV de prix. On le fabrique avec un simulateur
(mouvement brownien géométrique = une courbe de prix aléatoire réaliste).

```bash
# dur=1   -> 1 journée de bourse (~100 points, idéal pour tester vite)
# file=.. -> où écrire le fichier généré
./run.sh --generate dur=1 file=data/small.csv
```

Vérifie que le fichier est bien créé :

```bash
wc -l data/small.csv    # affiche le nombre de lignes (doit être > 0)
```

> Pour un jeu plus gros et plus réaliste : `./run.sh --generate dur=7 file=data/historic.csv`
> (7 jours). Mais c'est plus long à simuler (voir la note sur `--fast` plus bas).

---

## 6. Lancer la simulation 🎯

```bash
./run.sh --train data/small.csv
```

Ce que fait cette commande, dans l'ordre :

1. **Compile** le moteur C++ (`make`) → crée le binaire `src_cpp/main`.
2. **Lance** `main.py`, qui démarre :
   - le **broker** (chef d'orchestre entre C++ et les agents),
   - **3 agents** de trading (portefeuilles de 1000€, 2000€, 500€).
3. Le C++ envoie les prix tick par tick, les agents achètent/vendent.

⏱️ Avec `dur=1`, ça prend **~20 secondes**. Le terminal reste calme :
c'est normal, **tous les détails partent dans un fichier log**, pas à l'écran.

---

## 7. Voir ce qui se passe (les logs)

Toute l'activité (broker, agents, C++) est écrite dans `src_cpp/bourse.log`.

**Pendant** que ça tourne, ouvre un **2ᵉ terminal WSL** et suis en direct :

```bash
cd /mnt/c/Users/X515/Documents/GitHub/TradeAI
tail -f src_cpp/bourse.log     # défile en temps réel ; Ctrl+C pour arrêter de suivre
```

**Après** l'exécution, pour vérifier que tout a bien marché :

```bash
grep "Fin. Wallet" src_cpp/bourse.log      # portefeuilles finaux des 3 agents
grep -c "TICK;"    src_cpp/bourse.log       # nombre de ticks traités (doit être > 0)
grep -iE "Traceback|Error" src_cpp/bourse.log   # doit ne RIEN afficher
```

✅ **Si ça marche**, tu verras 3 lignes `Fin. Wallet` avec des montants
**différents** de 1000/2000/500 → preuve que les agents ont tradé.

---

## 8. Nettoyer (optionnel)

```bash
./run.sh --clean    # supprime le binaire compilé et les fichiers générés
```

---

## 🆘 Problèmes fréquents (et ce que j'ai rencontré)

| Message d'erreur | Cause | Solution |
|---|---|---|
| `./run.sh: cannot execute: required file not found` | `run.sh` a des fins de ligne Windows (CRLF) | Corrigé via `.gitattributes`. Sinon : `sed -i 's/\r$//' run.sh` |
| `pip: command not found` | pip pas installé | `sudo apt install python3-pip` |
| `externally-managed-environment` | Ubuntu bloque pip par défaut | Ajouter `--break-system-packages` à la commande pip |
| `No such file or directory: './src_cpp/main'` | Le C++ n'a pas été compilé | Passer par `./run.sh --train ...` (il compile), pas `python3 main.py` directement |
| `Fichier introuvable` (dans le log) | Aucun fichier de données passé au C++ | Toujours donner un fichier : `./run.sh --train data/small.csv` |
| `python: command not found` | Sous Linux c'est `python3` | Utiliser `python3`, jamais `python` |

---

## ⚠️ Note importante : n'utilise PAS `--fast`

L'option `--fast` supprime la pause entre les ticks côté C++. Or toute la
synchronisation repose sur cette pause : sans elle, le moteur termine **avant**
de recevoir les ordres des agents → **blocage (deadlock)**.

👉 Lance **sans** `--fast` tant que ce bug n'est pas corrigé.

---

## 📋 Récapitulatif ultra-court

```bash
# --- Une seule fois ---
sudo apt update && sudo apt install -y build-essential python3-pip
cd /mnt/c/Users/X515/Documents/GitHub/TradeAI
pip install --break-system-packages -r requirements.txt

# --- À chaque fois ---
./run.sh --generate dur=1 file=data/small.csv   # 1) générer les données
./run.sh --train data/small.csv                 # 2) lancer la simu
grep "Fin. Wallet" src_cpp/bourse.log           # 3) voir le résultat
```
