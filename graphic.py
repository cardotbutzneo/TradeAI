import matplotlib.pyplot as plt

def price_graph(price_lists: list, stock_ids: list):
    plt.xlabel("Time")
    plt.ylabel("Stock price")
    plt.grid(True)

    for prices, stock_id in zip(price_lists, stock_ids):
        x = list(range(len(prices)))
        y = prices
        plt.plot(x, y, label=stock_id)

    plt.show()

def Ai_graph(data : list[int,float])->None:
    X, Y = zip(*data)
    plt.plot(X, Y)
    plt.xlabel("Temps")
    plt.ylabel("Argent (€)")
    plt.grid(True)
    plt.show()
