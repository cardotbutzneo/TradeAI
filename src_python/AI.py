import numpy as np

class AI:
    def __init__(self, wallet: float, portfolio : dict, tolerance: float = 0.20):
        self.wallet = wallet
        self.tolerance = tolerance
        self.portfolio = portfolio # {FR001 : [date,prix_achat,quantite]}
        self.history = []
        self.global_value = wallet 

    def _(self, curent_price : dict):
        for stock in curent_price.keys():
                    
            # Case 1: We don't own this stock yet -> buy initialization logic
            if stock not in self.portfolio.keys():
                qty = int(0.3 * self.wallet // curent_price[stock])
                if qty > 0:
                    return f'BUY;{stock};{qty}'
                continue

            avg_price = curent_price[stock]

            # Case 2: Take Profit (Sell)
            if curent_price[stock] > avg_price * (1 + self.tolerance):
                qty = self.portfolio[stock][2]
                if qty > 0:
                    return f"SELL;{stock};{qty}"    

            # Case 3: Buy the dip
            elif curent_price[stock] < avg_price * (1 - self.tolerance):
                qty = int(0.3 * self.wallet // stock.stock_price)
                if qty > 0:
                    return f"BUY;{stock};{qty}"

    def trade(self, curent_price : dict, strategie):
        """Analyze market status and execute buy/sell decisions. 
        Strategie must return one of the tree possible value :
        -1 to sell, 0 to pass, and 1 to buy
        """
        
                
    def refresh(self, curent_price : dict):
        """Refresh the curent gain of the IA at each confirmation"""
        total_amount = 0
        for val in curent_price.values():
            total_amount += val
        
        self.global_value = self.wallet + total_amount