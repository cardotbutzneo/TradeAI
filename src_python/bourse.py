from random import uniform
import numpy as np

class Stock:
    def __init__(self, ISIN_id: str, stock_price: float, quantity: int):
        self.ISIN_id = ISIN_id
        self.stock_price = stock_price
        self.quantity = quantity
    
    def buy(self, wallet: float, amount: int) -> float:
        if wallet < 0 or amount <= 0:
            return wallet
        cost = self.stock_price * amount
        if wallet >= cost:
            wallet -= cost
            self.quantity += amount
        return wallet
    
    def sell(self, wallet: float, amount: int) -> float:
        if wallet < 0 or amount <= 0:
            return wallet
        if self.quantity >= amount:
            wallet += amount * self.stock_price
            self.quantity -= amount
        return wallet
    
class Market:
    def __init__(self, action_stock: list[Stock]):
        self.action_stock = action_stock
        # Automatically set up history for the stocks given to the market
        self.history = {stock.ISIN_id: [stock.stock_price] for stock in action_stock}

    def refresh(self):
        for stock in self.action_stock:
            history = self.history[stock.ISIN_id]
            current_price = history[-1]
            
            # --- GEOMETRIC BROWNIAN MOTION ---
            drift = 0.001       # Small positive daily upward trend (0.1%)
            volatility = 0.02   # 2% standard daily volatility
            
            # The standard formula for stock market simulation
            random_shock = np.random.normal(0, 1)
            price_change = current_price * (drift + volatility * random_shock)
            
            new_price = max(current_price + price_change, 0.01)
            
            stock.stock_price = new_price
            history.append(new_price)

    def daily_variation(self, stock: Stock) -> float:
        """Return the market variation compared to the previous tick (Daily Change)."""
        history = self.history[stock.ISIN_id]
        if len(history) < 2:
            return 0.0
        
        previous = history[-2]
        current = history[-1]
        return ((current - previous) / previous) * 100

    def print_market(self):
        print("\n--- Live Market Status ---")
        for stock in self.action_stock:
            var = self.daily_variation(stock)
            print(f"ID: [{stock.ISIN_id}] | Price: {stock.stock_price:.2f} $ | Change: {var:+.2f}%")