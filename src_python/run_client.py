import asyncio
import sys
import websockets
from AI import Stock, AI

"""FIle containing the function to run a client that connects to the broker and receives ticks and sends orders.
- run_client(url_tick: str, url_ordre: str, agent: AI, agent_id: str): Connects to the broker and handles ticks and orders for a given agent.
"""

async def run_client(url_tick: str, url_ordre: str,
                     agent: AI, agent_id: str):
    await asyncio.sleep(0.5)
    stock_dict: dict[str, Stock] = {}

    async with websockets.connect(url_tick)   as ws_tick, \
               websockets.connect(url_ordre)  as ws_ordre:

        # S'enregistre auprès du broker
        await ws_ordre.send(agent_id)
        confirmation = await ws_ordre.recv()  # attend la confirmation du broker

        if confirmation == f"REGISTERED;{agent_id}":
            print(f"[{agent_id}] Enregistré avec succès", file=sys.stderr)
        else:
            print(f"[{agent_id}] Erreur d'enregistrement : {confirmation}", file=sys.stderr)
            return

        async for tick in ws_tick:
            if tick == "STOP": break
            if not tick.startswith("TICK;"): continue

            # Accumule l'historique
            parts = tick.split(";")
            date  = parts[1]
            for item in parts[2].split(","):
                if not item: continue
                ticker, price, volume = item.split(":")
                if ticker not in stock_dict:
                    stock_dict[ticker] = Stock(ticker=ticker)
                    agent.portfolio[ticker] = [date, -1, 0]
                stock_dict[ticker].historic_price.append(float(price))
                stock_dict[ticker].historic_quantity.append(int(volume))
                stock_dict[ticker].total_quantity += int(volume)

            decisions = agent.trade(stock_dict)

            print(f"[Python-Debug] [{agent_id=}] decision : {decisions}", file=sys.stderr)

            if decisions == ["PASS"]:
                await ws_ordre.send("PASS")
                await ws_ordre.recv()  # ACK ignoré pour PASS
                continue

            await ws_ordre.send("|".join(decisions))
            ack = await ws_ordre.recv()
            print(f"[{agent_id}] ACK reçu : {ack}", file=sys.stderr)

            # Mise à jour portfolio
            for idx, decision in enumerate(decisions):
                parts_d          = decision.split(";")
                action, stock, quantity = parts_d[0], parts_d[1], int(parts_d[2])
                if "OK" in ack:
                    nouveau_cash = float(ack.split(";")[3]) if len(ack.split(";")) > 3 else agent.wallet
                    agent.wallet = nouveau_cash
                    if action == "BUY":
                        agent.portfolio[stock][2] += quantity
                        agent.portfolio[stock][1]  = stock_dict[stock].current_price
                    elif action == "SELL":
                        agent.portfolio[stock][2] -= quantity
                        agent.portfolio[stock][1]  = stock_dict[stock].current_price

        print(f"[{agent_id}] Fin. Wallet : {agent.wallet:.2f}€", file=sys.stderr)