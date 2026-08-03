import asyncio
import websockets
from .AI import Stock, AI
from .dataBase import Database
from .utils.utils import Return_code
from .utils.logger import logger

"""File containing the function to run a client that connects to the broker and receives ticks and sends orders."""

def verifier_connexion_cpp(tick, agent_id):
    if tick.startswith("REGISTER;"):
        parts = tick.split(";")
        if parts[1] == "OK":
            logger.info("Broker", f"Client {agent_id} bien enregistrée aupres du C++")
            return True
    else :
        logger.warn("Broker", f"Authentification de {agent_id} aupres du C++ a échoué")
        return False

async def run_client(url_tick: str, url_ordre: str,
                     agent: AI, agent_id: str, db: Database):
    await asyncio.sleep(0.5)
    stock_dict: dict[str, Stock] = {}

    async with websockets.connect(url_tick)   as ws_tick, \
               websockets.connect(url_ordre)  as ws_ordre:

        # S'enregistre auprès du broker
        await ws_ordre.send(f"{agent_id};{agent.wallet}")
        confirmation = await ws_ordre.recv()  # attend la confirmation du broker

        if confirmation == f"REGISTERED;{agent_id};OK":
            logger.info(f"{agent_id}", f"Enregistré avec succès auprès du serveur")
        else:
            logger.info(f"{agent_id}", f"Erreur d'enregistrement : {confirmation}")

        
        async for message in ws_tick:
            if message == "STOP":
                break

            if message.startswith("REGISTER;"):
                if not verifier_connexion_cpp(message, agent_id):
                    return Return_code.FAIL_CONNECTION
                continue

            if not message.startswith("TICK;"):
                continue

            parts = message.split(";")
            if len(parts) < 3:
                logger.warn(agent_id, f"Tick invalide reçu : {message}")
                continue

            date = parts[1]
            for item in parts[2].split(","):
                if not item:
                    continue
                fields = item.split(":")
                if len(fields) != 3:
                    logger.warn(agent_id, f"Tick mal formé : {item}")
                    continue
                ticker, price_str, volume_str = fields
                try:
                    price = float(price_str)
                    volume = int(volume_str)
                except ValueError:
                    logger.warn(agent_id, f"Tick contient des valeurs invalides : {item}")
                    continue

                if ticker not in stock_dict:
                    stock_dict[ticker] = Stock(ticker=ticker)
                    agent.portfolio[ticker] = [date, -1, 0]

                stock = stock_dict[ticker]
                stock.historic_price.append(price)
                stock.historic_quantity.append(volume)
                stock.total_quantity += volume

            decisions = agent.trade(stock_dict)
            logger.info(agent_id, f"Décision : {decisions}")

            if decisions == ["PASS"]:
                await ws_ordre.send("PASS")
                await ws_ordre.recv()
                continue

            await ws_ordre.send("|".join(decisions))
            ack = await ws_ordre.recv()
            logger.info(agent_id, f"ACK reçu : {ack}")

            await update_portfolio(agent_id, decisions, ack, agent, stock_dict, db)

        logger.info(agent_id, f"Fin. Wallet : {agent.wallet:.2f}€")

async def update_portfolio(agent_id: str,
                           decisions: list[str],
                           ack: str,
                           agent: AI,
                           stock_dict: dict[str, Stock],
                           db: Database):
    # Le C++ répond avec une ligne ACK par ordre envoyé, jointes par "|" dans
    # le même ordre que `decisions` (voir process_order_line côté C++ et le
    # dépilage par nombre d'ordres dans broker.handler_ordres). Chaque ACK ne
    # concerne QUE la décision de même index : il ne faut jamais appliquer un
    # seul statut/cash à tout le lot, sinon un rejet ou un cash mal aligné
    # sur un ordre contamine les autres ordres du même tour.
    ack_segments = ack.split("|")
    if len(ack_segments) != len(decisions):
        logger.warn(agent_id, f"Décalage ACK/décisions ({len(ack_segments)} ACK pour {len(decisions)} décisions) : {ack}")

    for decision, ack_segment in zip(decisions, ack_segments):
        action, stock_symbol, quantity_str = decision.split(";")
        quantity = int(quantity_str)

        parts = ack_segment.split(";")
        if len(parts) < 3:
            logger.warn(agent_id, f"ACK mal formé : {ack_segment}")
            continue
        status = parts[2]

        if status != "OK":
            logger.warn(agent_id, f"Ordre rejeté par le moteur : {ack_segment}")
            continue

        if len(parts) >= 4:
            try:
                agent.wallet = float(parts[3])
            except ValueError:
                logger.warn(agent_id, f"Impossible de lire le cash dans ACK : {parts[3]}")

        if stock_symbol not in stock_dict:
            logger.warn(agent_id, f"Stock inconnu pour mise à jour : {stock_symbol}")
            continue

        stock = stock_dict[stock_symbol]
        price = stock.current_price

        if action == "BUY":
            agent.portfolio[stock_symbol][2] += quantity
            agent.portfolio[stock_symbol][1] = price
        elif action == "SELL":
            agent.portfolio[stock_symbol][2] = max(0, agent.portfolio[stock_symbol][2] - quantity)
            agent.portfolio[stock_symbol][1] = price

        db.insert_trade(agent_id, stock_symbol, action, price, quantity, agent.wallet)
        db.update_portfolio(agent_id, stock_symbol,
                            agent.portfolio[stock_symbol][2],
                            agent.portfolio[stock_symbol][1])
