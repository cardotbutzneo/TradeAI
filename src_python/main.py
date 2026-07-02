import sys
import subprocess
from AI import AI, Stock
from graphic import price_graph

def run_simulation_stream():
    process = subprocess.Popen(
        ['./main'], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    ai_agent = AI(wallet=1000.0, portfolio={}, tolerance=0.01)
    stock_dict : dict[str, Stock] = {}
    t = 0

    while True:
        line = process.stdout.readline().strip()  # UN seul point de lecture
        if not line or line == "STOP":
            break

        print(f"[PYTHON-DEBUG] recu du cpp : {line}", file=sys.stderr)

        if line.startswith("TICK;"):
            parts = line.split(";")
            date = parts[1]
            for item in parts[2].split(","):
                if item:
                    ticker, price, volume = item.split(":")
                    if ticker not in stock_dict:
                        stock_dict[ticker] = Stock(ticker=ticker)
                        ai_agent.portfolio[ticker] = [date, -1, 0]

                    # Accumule l'historique
                    stock_dict[ticker].historic_price.append(float(price))
                    stock_dict[ticker].historic_quantity.append(int(volume))
                    stock_dict[ticker].total_quantity += int(volume)
                

            all_decision = ai_agent.trade(stock_dict)
            #print(f"[Python-Debug] Listes des ordres : {all_decision}", file=sys.stderr)

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
            confirm_flag = [False] * (len(confirmation.split("|")) - 1)

            for sub_conf, i in zip(confirmation.split("|"), range(len(confirm_flag))):
                if not sub_conf:
                    continue
                if sub_conf.startswith("ACK;OK"):
                    nouveau_cash = float(sub_conf.split(";")[2])
                    ai_agent.wallet = nouveau_cash
                    confirm_flag[i] = True # on actualise les flags pour savoir si l'action a été validé par le cpp 

                    print(f"[Python-Debug] nouveau cash : {ai_agent.wallet}", file=sys.stderr)
                    print(f"[Python] Order ACCEPTED: {sub_conf}", file=sys.stderr)
                elif sub_conf.startswith("ACK;REJECT"):
                    print(f"[Python] Order REJECTED: {sub_conf}", file=sys.stderr)

            # Mise à jour du portfolio après confirmation
            for idx, decision in enumerate(all_decision):
                parts_d = decision.split(';')
                action, stock, quantity = parts_d[0], parts_d[1], int(parts_d[2])
                if action == "BUY" and idx < len(confirm_flag) and confirm_flag[idx]:
                    ai_agent.portfolio[stock][2] += quantity
                    ai_agent.portfolio[stock][1] = stock_dict[stock].current_price
                elif action == "SELL" and confirm_flag[idx]:
                    ai_agent.portfolio[stock][2] -= quantity
                    ai_agent.portfolio[stock][1] = stock_dict[stock].current_price

            ai_agent.refresh(stock_dict)
            print(f"[Python-Debug] Portfolio: {ai_agent.portfolio}", file=sys.stderr)
            t += 1

    process.stdin.close()
    print(f"Différence de taille : {len(stock_dict['GOOG'].historic_price) - len(stock_dict['AMZ'].historic_price)} ({len(stock_dict['GOOG'].historic_price)} - {len(stock_dict['AMZ'].historic_price)})")
    process.wait()
    print("\n[Python] Flux terminé.", file=sys.stderr)
    price_graph(list(stock_dict.values()))

if __name__ == "__main__":
    run_simulation_stream()