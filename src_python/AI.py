import numpy as np
import sys
from random import randint
import train_AI

"""AI.py — Contains the AI class and related classes for stock trading simulation.
- Stock: Represents a stock with its ticker, historical prices, and quantities."""

# currency detect by the programm
ALLOWED_CURRENCY = ["USD", "EUR", "GBD", "JPY"]

def hamming_distance(s1, s2):
    if len(s1) != len(s2):
        return float('inf') # Retourne l'infini si les longueurs diffèrent au lieu de crasher
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

class Transaction : 
    """Représente une transaction sur le carnet d'ordre"""
    def __init__(self, ticker : str, montant : float, quantite : int, currency : str,
                 buyer : str, seller : str):
        pass

class Stock:
    def __init__(self, ticker: str, historic_price: list[float] = None, 
                 historic_quantity: list[int] = None, total_quantity: int = 0,
                 currency : str = "EUR"):
        
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
    
    def __init__(self, wallet: float, portfolio : dict, nn : train_AI.NeuralNetwork, tolerance: float = 0.20):
        self.wallet = wallet
        self.tolerance = tolerance
        self.portfolio = portfolio # {FR001 : [date,prix_achat,quantite]}
        self.history = []
        self.global_value = wallet 
        self._nn : train_AI.NeuralNetwork = nn
        self._is_train = False

    def strat(self, stock: Stock) -> str | None:
        features = compute_features(stock)
        if features is None:
            return None

        X = features.reshape(1, -1)
        decision_idx = self._nn.predict(X)[0]

        labels = ["PASS", "BUY", "SELL"]
        if labels[decision_idx] == "PASS":
            return None

        qte = int(0.2 * self.wallet / stock.current_price)
        if qte <= 0: return None
        return f"{labels[decision_idx]};{stock.ticker};{qte}"


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
        else : return f"SELL;{stock.ticker};{self.portfolio[stock.ticker][2]}"


    def trade(self, stock_list : dict[str, Stock], strategie = strat1):
        """Analyze market status and execute buy/sell decisions. """
        decisions = []
        for ticker, stock in stock_list.items():
            decision = strategie(stock)
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

def compute_features(stock: Stock) -> np.ndarray:
    def compute_rsi(prices: list[float], period: int = 14) -> float:
        # fonction pour les calculs
        deltas = np.diff(prices[-period-1:])
        gains  = np.where(deltas > 0, deltas, 0).mean()
        losses = np.where(deltas < 0, -deltas, 0).mean()
        if losses == 0: return 1.0
        rs = gains / losses
        return 1 - (1 / (1 + rs))
    def compute_ema(prices: np.ndarray, period: int) -> float:
        alpha = 2.0 / (period + 1)
        ema = prices[0]
        for p in prices[1:]:
            ema = alpha * p + (1 - alpha) * ema
        return ema

    def compute_macd(prices: np.ndarray) -> float:
        if len(prices) < 26:
            return 0.0
        ema12 = compute_ema(prices[-26:], 12)
        ema26 = compute_ema(prices[-26:], 26)
        return (ema12 - ema26) / prices[-1]
    
    prices = np.array(stock.historic_price)
    
    if len(prices) < 26:  # pas assez d'historique
        return None

    prix_min  = prices.min()
    prix_max  = prices.max()
    prix_norm = (prices[-1] - prix_min) / (prix_max - prix_min + 1e-9)

    variation_1j = (prices[-1] - prices[-2])  / prices[-2]
    variation_5j = (prices[-1] - prices[-6])  / prices[-6]
    rsi          = compute_rsi(prices)
    macd         = compute_macd(prices)

    return np.array([prix_norm, variation_1j, variation_5j, rsi, macd])
