import sys
import subprocess
# On n'importe PLUS ni Market ni Stock de Python !
from AI import AI 
from graphic import Ai_graph

def run_simulation_stream():
    process = subprocess.Popen(
        ['./main'], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    ai_agent = AI(wallet=1000.0, portfolio={}, tolerance=0.10)
    ai_history_data = []
    t = 0

    while True:
        line = process.stdout.readline().strip()  # UN seul point de lecture
        if not line or line == "STOP":
            break

        print(f"[PYTHON-DEBUG] recu du cpp : {line}", file=sys.stderr)

        if line.startswith("TICK;"):
            parts = line.split(";")
            date = parts[1]
            current_prices = {}
            for item in parts[2].split(","):
                if item:
                    ticker, price = item.split(":")
                    current_prices[ticker] = float(price)
                    if ticker not in ai_agent.portfolio:
                        ai_agent.portfolio[ticker] = [date, -1, 0]

            all_decision = ai_agent.trade(current_prices)
            print(f"[Python-Debug] Listes des ordres : {all_decision}", file=sys.stderr)

            if all_decision == ["PASS"]:
                process.stdin.write("PASS\n")
                process.stdin.flush()
                # Pas d'ACK attendu pour PASS, on reboucle directement
                continue

            combined_orders = "|".join(all_decision)
            process.stdin.write(f"{combined_orders}\n")
            process.stdin.flush()

            # On attend exactement 1 ligne d'ACK groupé
            confirmation = process.stdout.readline().strip()
            print(f"[PYTHON-DEBUG] confirmation : {confirmation}", file=sys.stderr)

            for sub_conf in confirmation.split("|"):
                if not sub_conf:
                    continue
                if sub_conf.startswith("ACK;OK"):
                    nouveau_cash = float(sub_conf.split(";")[2])
                    ai_agent.wallet = nouveau_cash
                    print(f"[Python] Order ACCEPTED: {sub_conf}", file=sys.stderr)
                elif sub_conf.startswith("ACK;REJECT"):
                    print(f"[Python] Order REJECTED: {sub_conf}", file=sys.stderr)

            # Mise à jour du portfolio après confirmation
            for decision in all_decision:
                parts_d = decision.split(';')
                action, stock, quantity = parts_d[0], parts_d[1], int(parts_d[2])
                if stock in current_prices:
                    ai_agent.portfolio[stock][1] = current_prices[stock]
                    ai_agent.portfolio[stock][2] += quantity if action == "BUY" else -quantity

            ai_agent.refresh(current_prices)
            print(f"[Python-Debug] Portfolio: {ai_agent.portfolio}", file=sys.stderr)
            ai_history_data.append([t, ai_agent.global_value])
            t += 1

    process.stdin.close()
    process.wait()
    print("\n[Python] Flux terminé.", file=sys.stderr)
    Ai_graph(ai_history_data)

if __name__ == "__main__":
    run_simulation_stream()