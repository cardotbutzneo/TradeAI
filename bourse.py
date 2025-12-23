#### Market simulation ###

from random import uniform
import numpy as np

## Market classes ##

class Stock:
    def __init__(self, ISIN_id : str, stock_price : float, quantity : int):
        self.ISIN_id = ISIN_id
        self.stock_price = stock_price
        self.quantity = quantity
    
    def buy(self, wallet : float, amount : int)->float:
        if wallet < 0 or amount <= 0:
            return wallet
        cost = self.stock_price * amount
        if wallet >= cost:
            wallet -= cost
            self.purchase_price = self.stock_price
            self.quantity += amount

        return wallet
    
    def sell(self, wallet : float, amount : int)->float:
        if wallet < 0 or amount <= 0:
            return wallet
        
        if self.quantity >= amount:
            wallet += amount * self.stock_price
            self.quantity -= amount
            self.purchase_price = None

        return wallet
    
class Market: # market with 1 stock
    def __init__(self, action_stock : list[Stock], history : dict):
        self.action_stock = action_stock
        self.history = history # dict: ISIN -> list of prices

    def refresh(self):
        for stock in self.action_stock:
            history = self.history[stock.ISIN_id]
            change_price(history, stock)

    def print_Market(self):
        for stock in self.action_stock:
            print(f"id : [{stock.ISIN_id}]    price : {stock.stock_price:.2f} $     avalable quantity : {stock.quantity}")


## calculus function ##

def change_price(stock_history: list, stock: Stock):
    if len(stock_history) == 0:
        stock_history.append(stock.stock_price)
        return

    mu = stock_history[-1]
    sigma = mu * 0.1  # 3.5% volatility

    new_price = np.random.normal(mu, sigma)

    stock.stock_price = max(new_price, 0.01)
    stock_history.append(stock.stock_price)
