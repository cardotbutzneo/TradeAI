import numpy as np
import sys
from random import randint

class Stock:
    def __init__(self, ticker: str, historic_price: list[float] = None, 
                 historic_quantity: list[int] = None, total_quantity: int = 0):
        
        self.ticker            = ticker       
        self.historic_price    = historic_price    if historic_price    is not None else []
        self.historic_quantity = historic_quantity if historic_quantity is not None else []
        self.total_quantity    = total_quantity

    @property
    def current_price(self) -> float:
        return self.historic_price[-1] if self.historic_price else 0.0

    @property
    def total_value(self) -> float:
        return float(np.dot(self.historic_price, self.historic_quantity))
    
class AI:
    def __init__(self, wallet: float, portfolio : dict, tolerance: float = 0.20):
        self.wallet = wallet
        self.tolerance = tolerance
        self.portfolio = portfolio # {FR001 : [date,prix_achat,quantite]}
        self.history = []
        self.global_value = wallet 

    def strat1(self, stock: Stock) -> str | None:
        price = stock.current_price

        if self.portfolio[stock.ticker][1] == -1:
            qty = int(0.3 * self.wallet // price)
            if qty > 0: return f"BUY;{stock.ticker};{qty}"

        avg_price = np.mean(stock.historic_price)

        if price > avg_price * (1 + self.tolerance):
            qty = self.portfolio[stock.ticker][2]
            if qty > 0: return f"SELL;{stock.ticker};{qty}"

        elif price < avg_price * (1 - self.tolerance):
            qty = int(0.3 * self.wallet // price)
            if qty > 0: return f"BUY;{stock.ticker};{qty}"

        return None
    
    def strat2(self, stock : Stock , price : float) :
        qty = int(0.2*self.wallet // price)
        if randint(0,1) == 0 : return f"BUY;{stock.ticker};{qty}"
        else : return f"SELL;{stock.ticker};{qty}"


    def trade(self, stock_list : dict[str, Stock], strategie = strat1):
        """Analyze market status and execute buy/sell decisions. """
        decisions = []
        for ticker, stock in stock_list.items():
            decision = self.strat2(stock, stock.current_price)
            if decision != "PASS" and decision != None:
                decisions.append(decision)
        return decisions if decisions else ["PASS"]
                
    def refresh(self, stock_dict: dict[str, Stock]):
        """Refresh the total global value of the AI's portfolio."""
        total_assets = sum(
        stock.historic_price[-1] * self.portfolio[ticker][2]
        for ticker, stock in stock_dict.items()
        if ticker in self.portfolio
    )
        self.global_value = self.wallet + total_assets