import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from AI import Stock

def price_graph(stock_list: list[Stock]):
    stock_list = list(stock_list)
    fig, axes = plt.subplots(len(stock_list), 1, figsize=(14, 5 * len(stock_list)))
    
    if len(stock_list) == 1:
        axes = [axes]

    for ax, stock in zip(axes, stock_list):
        prices = np.array(stock.historic_price, dtype=float)
        
        if len(prices) < 4:
            print(f"Pas assez de données pour {stock.ticker}")
            continue

        # Regroupe les ticks par bougie (ex: 1 bougie = 12 ticks de 5min = 1h)
        candle_size = 12
        nb_candles  = len(prices) // candle_size

        opens, closes, highs, lows = [], [], [], []
        for i in range(nb_candles):
            chunk = prices[i * candle_size : (i + 1) * candle_size]
            opens.append(chunk[0])
            closes.append(chunk[-1])
            highs.append(chunk.max())
            lows.append(chunk.min())

        opens  = np.array(opens)
        closes = np.array(closes)
        highs  = np.array(highs)
        lows   = np.array(lows)
        x      = np.arange(nb_candles)

        # Couleur : vert si hausse, rouge si baisse
        colors = ['green' if c >= o else 'red' for o, c in zip(opens, closes)]

        # Mèches (high/low)
        for i in range(nb_candles):
            ax.plot([x[i], x[i]], [lows[i], highs[i]], color=colors[i], linewidth=1)

        # Corps de la bougie
        bodies = np.abs(closes - opens)
        bottoms = np.minimum(opens, closes)
        ax.bar(x, bodies, bottom=bottoms, color=colors, width=0.6, linewidth=0)

        ax.set_title(f"{stock.ticker} — {nb_candles} bougies")
        ax.set_ylabel("Prix (€)")
        ax.set_xlabel("Bougie")
        ax.grid(True, alpha=0.3)

        # Légende
        legend_handles = [
            Line2D([0], [0], color='green', linewidth=4, label='Hausse'),
            Line2D([0], [0], color='red',   linewidth=4, label='Baisse'),
        ]
        ax.legend(handles=legend_handles, loc='upper left')

    plt.tight_layout()
    plt.show()
