### Simulation de l'IA ###
from bourse import *
from calculus import *

class AI:
    
    def __init__(self, wallet : float, portfolio : dict[str,int], global_value : float, tolerance : float):
        self.wallet = wallet # {id : [buy_price, quantity],...}
        self.portfolio = portfolio # dict of all stock bought by AI 
        self.global_value = global_value # value of the portolio (o(1) complexity)
        self.tolerance = tolerance

    def get_information(self, market: Market):
        for stock in market.action_stock:
            stock: Stock

            if stock.purchase_price is None:
                continue

            if stock.stock_price > stock.purchase_price * (1 + self.tolerance): # sell
                self.wallet = stock.sell(self.wallet, stock.quantity)
                print(f"L'IA vent - {self.wallet} $")
            
            elif stock.stock_price < stock.purchase_price * (1 - self.tolerance): # buy
                self.wallet = stock.buy(self.wallet,stock.quantity)
                print(f"L'IA achete - {self.wallet} $")

            self.global_value = self.wallet

            for stock in market.action_stock:
                if stock.ISIN_id in self.portfolio:
                    self.global_value += stock.stock_price * self.portfolio[stock.ISIN_id]

            self.tolerance = self.risk(
                market.history[stock.ISIN_id],
                self.tolerance
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

    def print_portfolio(self):
        for id,value in self.portfolio.items():
            print(f"ID : {id} - value : {value}")

