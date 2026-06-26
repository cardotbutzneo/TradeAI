import sys
import subprocess
# On n'importe PLUS ni Market ni Stock de Python !
from AI import AI 
from graphic import Ai_graph

def run_simulation_stream():

    process = subprocess.Popen(
        ['./main'], 
        stdin=subprocess.PIPE,  # Ouvre le Pipe N°1 (Python -> C++)
        stdout=subprocess.PIPE, # Ouvre le Pipe N°2 (C++ -> Python)
        text=True
    )

    ai_agent = AI(wallet=1000.0, portfolio={}, tolerance=0.10)
    ai_history_data = []
    t = 0

    for line in process.stdout:
        line = line.strip()
        print(f"[PYTHON-DEBUG] recu du cpp : {line}", file=sys.stderr)
        
        if line == "STOP" or not line:
            break
            
        if line.startswith("TICK;"):
            parts = line.split(";")
            date = parts[1]
            market_data_raw = parts[2]
            
            current_prices = {}
            for item in market_data_raw.split(","):
                if item: # Évite le dernier élément vide après la virgule
                    ticker, price = item.split(":")
                    current_prices[ticker] = float(price)

            decision = ai_agent.trade(current_prices) 

            if decision and decision != "PASS":

                process.stdin.write(f"{decision}\n")
                process.stdin.flush()

                confirmation = process.stdout.readline().strip()

                if confirmation.startswith("ACK;OK"):
                    nouveau_cash = float(confirmation.split(";")[2])
                    ai_agent.wallet = nouveau_cash
                    ai_agent.refresh(current_prices)
                    print(f"[Python] Ordre exécuté avec succès. Nouveau cash : {nouveau_cash}")
                else:
                    print(f"[Python] Ordre REJETÉ par le C++ : {confirmation}")
            else:
                # Si PASS, on dit juste au C++ qu'on ne fait rien pour qu'il avance d'un jour
                process.stdin.write("PASS\n")
                process.stdin.flush()
            
            ai_history_data.append([t, ai_agent.global_value])
            t += 1
    
    process.stdin.close()
    process.wait()

    # 5. Présentation des résultats une fois le flux coupé
    print("\n[Python] Flux terminé. Génération des graphiques de performance...", file=sys.stderr)
    Ai_graph(ai_history_data)

if __name__ == "__main__":
    run_simulation_stream()