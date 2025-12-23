### Simulation de l'IA ###
from bourse import *
from calculus import *

class AI:
    
    def __init__(self, wallet : float, portfolio : dict[str, dict[int,float]], global_value : float, tolerance : float):
        self.wallet = wallet # current value on the market
        self.portfolio = portfolio # {id : {"quantity : ","purchase price"},...} 
        self.global_value = global_value # value of the portolio (o(1) complexity)
        self.tolerance = tolerance

    def get_information(self, market: Market):
        for stock in market.action_stock:
            stock: Stock

            if stock.ISIN_id not in self.portfolio:
                continue

            avg_price = self.portfolio[stock.ISIN_id]["avg_price"]

            if stock.stock_price > avg_price * (1 + self.tolerance): #sell
                qty = self.portfolio[stock.ISIN_id]["quantity"]
                self.wallet = stock.sell(self.wallet, qty)
                del self.portfolio[stock.ISIN_id]

            elif stock.stock_price < self.portfolio[stock.ISIN_id]["avg_price"] * (1 - self.tolerance): # buy
                qty = int(0.3 * self.wallet // stock.stock_price)
                if qty > 0:
                    self.wallet = stock.buy(self.wallet, qty)
                    self.refresh_portfolio(stock.ISIN_id, qty, stock.stock_price)

        self.global_value = self.wallet
        for stock in market.action_stock:
            if stock.ISIN_id in self.portfolio:
                self.global_value += (
                    stock.stock_price *
                    self.portfolio[stock.ISIN_id]["quantity"]
                )       

    def risk(self, history: list, tolerance: float) -> float:
        if len(history) <= 20:
            return tolerance

        sigma_short = sigma(history[-12:])
        sigma_long = sigma(history[-20:])

        if sigma_short > 1.5 * sigma_long:
            return tolerance * 0.5
        else:
            return tolerance * 1.2

    def print_portfolio(self, market: Market):
        print("=== AI Portfolio ===")
        total_value = self.wallet

        for stock in market.action_stock:
            if stock.ISIN_id in self.portfolio:
                data = self.portfolio[stock.ISIN_id]
                qty = data["quantity"]
                avg_price = data["avg_price"]

                current_value = qty * stock.stock_price
                pnl = (stock.stock_price - avg_price) * qty

                total_value += current_value

                print(
                    f"{stock.ISIN_id} | "
                    f"Qty: {qty} | "
                    f"Avg: {avg_price:.2f} | "
                    f"Current: {stock.stock_price:.2f} | "
                    f"PnL: {pnl:+.2f}"
                )

        print(f"\nWallet: {self.wallet:.2f}")
        print(f"Total value: {total_value:.2f}")


    def refresh_portfolio(self, id: str, quantity: int, price: float):
        if id not in self.portfolio:
            # First buy
            self.portfolio[id] = {
                "quantity": quantity,
                "avg_price": price
            }
        else:
            old_q = self.portfolio[id]["quantity"]
            old_p = self.portfolio[id]["avg_price"]

            new_q = old_q + quantity
            new_p = (old_q * old_p + quantity * price) / new_q

            self.portfolio[id]["quantity"] = new_q
            self.portfolio[id]["avg_price"] = new_p

