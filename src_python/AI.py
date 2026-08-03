from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .train_AI import NeuralNetwork

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
    """Un agent de trading. `strategy` sélectionne le comportement de marché
    simulé (voir AI.STRATEGIES) ; `tolerance` règle la sensibilité de ce
    comportement (plus tolerance est faible, plus l'agent réagit vite)."""

    # Gestion du risque, partagée par toutes les stratégies :
    MAX_POSITION_PCT = 0.30   # jamais plus de 30% du portefeuille sur un seul titre
    TRADE_SIZE_PCT   = 0.15   # jamais plus de 15% du cash disponible en un seul ordre
    STOP_LOSS_PCT    = 0.15   # vente forcée si la position perd 15% depuis l'achat
    MEAN_WINDOW      = 20     # fenêtre glissante pour la moyenne mobile

    def __init__(self, wallet: float, portfolio: dict, nn: "NeuralNetwork" | None = None,
                 tolerance: float = 0.20, strategy: str = "mean_reversion"):
        self.wallet = wallet
        self.tolerance = tolerance
        self.portfolio = portfolio  # {FR001 : [date,prix_achat,quantite]}
        self.history = []
        self.global_value = wallet
        self.strategy = strategy
        self._nn: "NeuralNetwork" | None = nn
        self._is_train = False

    def _held_quantity(self, ticker: str) -> int:
        return self.portfolio[ticker][2] if ticker in self.portfolio else 0

    def _buy_quantity(self, stock: Stock) -> int:
        """Taille d'ordre réaliste : plafonnée par le cash dispo et par la
        part maximale qu'un titre peut représenter dans le portefeuille."""
        price = stock.current_price
        if price <= 0:
            return 0

        position_value = self._held_quantity(stock.ticker) * price
        max_position_value = self.MAX_POSITION_PCT * max(self.global_value, self.wallet)
        room = max_position_value - position_value
        if room <= 0:
            return 0

        budget = min(self.TRADE_SIZE_PCT * self.wallet, room, self.wallet)
        return int(budget // price)

    def _stop_loss_signal(self, stock: Stock) -> str | None:
        """Coupe une position perdante avant toute autre décision, comme le
        ferait un trader disciplinaire plutôt qu'un joueur qui espère."""
        ticker = stock.ticker
        if ticker not in self.portfolio:
            return None

        _, avg_price, qty = self.portfolio[ticker]
        if qty <= 0 or avg_price <= 0:
            return None

        if stock.current_price <= avg_price * (1 - self.STOP_LOSS_PCT):
            return f"SELL;{ticker};{qty}"
        return None

    def strat(self, stock: Stock) -> str | None:
        """Décision pilotée par le réseau de neurones entraîné."""
        features = compute_features(stock)
        if features is None or self._nn is None:
            return None

        X = features.reshape(1, -1)
        decision_idx = self._nn.predict(X)[0]

        labels = ["PASS", "BUY", "SELL"]
        label = labels[decision_idx]
        if label == "PASS":
            return None

        if label == "BUY":
            qty = self._buy_quantity(stock)
        else:
            qty = self._held_quantity(stock.ticker)

        if qty <= 0:
            return None
        return f"{label};{stock.ticker};{qty}"

    def strat_mean_reversion(self, stock: Stock) -> str | None:
        """Parie sur un retour à la moyenne mobile récente : achète quand le
        prix décroche sous sa tendance, revend progressivement quand il
        s'en écarte trop vers le haut (pas de tout-ou-rien)."""
        prices = stock.historic_price
        if len(prices) < self.MEAN_WINDOW:
            return None  # pas assez d'historique pour juger d'une tendance

        price = stock.current_price
        moving_avg = float(np.mean(prices[-self.MEAN_WINDOW:]))
        if moving_avg <= 0:
            return None

        deviation = (price - moving_avg) / moving_avg
        qty_held = self._held_quantity(stock.ticker)

        if deviation <= -self.tolerance:
            qty = self._buy_quantity(stock)
            if qty > 0:
                return f"BUY;{stock.ticker};{qty}"
        elif deviation >= self.tolerance and qty_held > 0:
            qty = max(1, qty_held // 2)  # prise de profit partielle
            return f"SELL;{stock.ticker};{qty}"

        return None

    def strat_momentum(self, stock: Stock) -> str | None:
        """Suit la tendance (MACD + variation sur 5 jours) plutôt que de
        parier contre elle : achète les titres qui accélèrent, sort dès que
        la dynamique se retourne."""
        features = compute_features(stock)
        if features is None:
            return None

        _, variation_1j, variation_5j, rsi, macd = features
        qty_held = self._held_quantity(stock.ticker)

        trend_up = macd > 0 and variation_5j > 0
        trend_down = macd < 0 and variation_5j < 0

        if trend_up and variation_1j > 0 and rsi < 0.8:
            qty = self._buy_quantity(stock)
            if qty > 0:
                return f"BUY;{stock.ticker};{qty}"
        elif (trend_down or rsi > 0.85) and qty_held > 0:
            return f"SELL;{stock.ticker};{qty_held}"

        return None

    def strat_rsi_contrarian(self, stock: Stock) -> str | None:
        """Trade les excès du RSI : achète en zone de survente, vend en
        zone de surachat. `tolerance` fixe la largeur de la zone neutre."""
        features = compute_features(stock)
        if features is None:
            return None

        _, _, _, rsi, _ = features
        qty_held = self._held_quantity(stock.ticker)

        oversold = 0.5 - self.tolerance
        overbought = 0.5 + self.tolerance

        if rsi <= oversold:
            qty = self._buy_quantity(stock)
            if qty > 0:
                return f"BUY;{stock.ticker};{qty}"
        elif rsi >= overbought and qty_held > 0:
            qty = max(1, qty_held // 2)  # prise de profit partielle
            return f"SELL;{stock.ticker};{qty}"

        return None

    STRATEGIES = {
        "mean_reversion": strat_mean_reversion,
        "momentum": strat_momentum,
        "rsi_contrarian": strat_rsi_contrarian,
        "neural_net": strat,
    }

    def trade(self, stock_list: dict[str, Stock], strategie=None):
        """Analyze market status and execute buy/sell decisions."""
        self.refresh(stock_list)
        fn = strategie or self.STRATEGIES.get(self.strategy, AI.strat_mean_reversion)

        decisions = []
        for ticker, stock in stock_list.items():
            decision = self._stop_loss_signal(stock) or fn(self, stock)
            if decision != "PASS" and decision is not None:
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
