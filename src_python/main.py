import sys
import subprocess
import AI
from train_AI import NeuralNetwork, build_dataset
from graphic import price_graph

def run_simulation_stream(filepath : str, mode = ""): # valeur a modifier à la main

    if mode != "--train" and mode != "--prod":
        print("Error : none mode find.")
        print("Please enter a mode : [--train | --dev]")
        exit(1)

    if mode == "--train":
        # Entraînement une fois avant la simulation
        nn = NeuralNetwork([5, 16, 8, 3])
        X, y = build_dataset(filepath)
        print(y.sum(axis=0))
        nn.train(X, y, epochs=10000, learning_rate=0.1)
    

    process = subprocess.Popen(
        ['./src_cpp/main', mode, filepath], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    # Puis on passe le réseau entraîné à l'AI
    ai_agent = AI.AI(wallet=1000.0, portfolio={}, nn=nn, tolerance=0.01)
    valeur_total : list[float] = []
    stock_dict : dict[str, AI.Stock] = {}
    t = 0

    while True:
        if t % 10 == 0:
            valeur_total.append(ai_agent.global_value)

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
                        stock_dict[ticker] = AI.Stock(ticker=ticker)
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

    print("-" * 10, "Résultat : ", "-" * 10)
    print(f"valeur intiale : {valeur_total[0]} | valeur finale : {valeur_total[-1]}")
    print(f"Variation de la valeur total : {((valeur_total[-1] - valeur_total[0]) / valeur_total[-1] * 100):.3g}%")

    process.stdin.close()
    process.wait()
    print("\n[Python] Flux terminé.", file=sys.stderr)
    price_graph(list(stock_dict.values()))

if __name__ == "__main__":
    print(sys.argv[1])
    mode = sys.argv[1]
    filepath = sys.argv[2]
    run_simulation_stream(filepath, mode)