import matplotlib.pyplot as plt

def price_graph(price_lists: list[list[float]], stock_ids: list[str]):
    """
    Plots the price history of multiple stocks cleanly on a single graph.
    """
    # 1. Clear any previous graphs out of memory and set a clean canvas size
    plt.figure(figsize=(10, 5))
    
    # 2. Add structural styling to make it look clean and professional
    plt.title("Stock Price Evolution", fontsize=14, fontweight='bold')
    plt.xlabel("Time (Ticks)", fontsize=11)
    plt.ylabel("Stock Price ($)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)  # Subtle, dashed gridlines

    # 3. Plot each stock's timeline
    for prices, stock_id in zip(price_lists, stock_ids):
        # Matplotlib automatically handles the x-axis index (0 to len-1) 
        # if you only pass it a y-axis array! No need to create a manual 'x' list.
        plt.plot(prices, label=stock_id, linewidth=2)

    # 4. Display the legend (crucial so you know which color belongs to which stock)
    plt.legend(loc="upper left")
    
    # 5. Render the layout beautifully and display
    plt.tight_layout()
    plt.show()
    plt.close() # Closes the window resource to prevent RAM leakage

def Ai_graph(data : list[int,float])->None:
    X, Y = zip(*data)
    plt.plot(X, Y)
    plt.xlabel("Temps")
    plt.ylabel("Argent (€)")
    plt.grid(True)
    plt.show()
