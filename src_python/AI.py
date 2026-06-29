import numpy as np
import sys
from random import randint

class Stock : 
    def __int__(self, ticker : str, historic_price : list[float], historic_quantity : list[int], total_quantity : int):
        self.ticker = ticker
        self.historic_price = historic_price
        self.historic_quantity = historic_quantity
        self.total_quantity = total_quantity
        self.total_value = np.sum(np.array(historic_price) * np.array(historic_quantity)) 

class AI:
    def __init__(self, wallet: float, portfolio : dict, tolerance: float = 0.20):
        self.wallet = wallet
        self.tolerance = tolerance
        self.portfolio = portfolio # {FR001 : [date,prix_achat,quantite]}
        self.history = []
        self.global_value = wallet 

    def strat1(self, stock : str, price : float):       
        # Case 1: We don't own this stock yet -> buy initialization logic
        if self.portfolio[stock][1] == -1 :
            qty = int(0.3 * self.wallet // price)
            if qty > 0:
                return f'BUY;{stock};{qty}'

        avg_price = price

        # Case 2: Take Profit (Sell)
        if price > avg_price * (1 + self.tolerance):
            qty = self.portfolio[stock][2]
            if qty > 0:
                return f"SELL;{stock};{qty}"    

        # Case 3: Buy the dip
        elif price < avg_price * (1 - self.tolerance):
            qty = int(0.3 * self.wallet // stock.stock_price)
            if qty > 0:
                return f"BUY;{stock};{qty}"
            
    def strat2(self, stock, price) :
        qty = int(0.2*self.wallet // price)
        if randint(0,1) == 0 : return f"BUY;{stock};{qty}"
        else : return f"SELL;{stock};{qty}"


    def trade(self, curent_price : dict, strategie = strat1):
        """Analyze market status and execute buy/sell decisions. """
        decisions = []
        for tiker, price in curent_price.items() :
            decision = self.strat2(tiker, price)
            if decision != "PASS" and decision != None:
                decisions.append(decision)
        return decisions if decisions else ["PASS"]
                
    def refresh(self, current_price: dict):
        """Refresh the total global value of the AI's portfolio."""
        total_assets_value = 0
        
        for ticker in self.portfolio.keys():
            if ticker in current_price:
                quantity = self.portfolio[ticker][2]
                live_price = current_price[ticker]
                
                total_assets_value += live_price * quantity

        self.global_value = self.wallet + total_assets_value