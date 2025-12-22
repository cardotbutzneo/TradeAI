import matplotlib.pyplot as plt

def price_graph(price_list : list, stock_id : str): 
    
    x = [t for t in range(len(price_list))]
    y = [price for price in price_list]

    plt.xlabel("time")
    plt.ylabel(f"Stock [{stock_id}] price")
    plt.grid(True)
    plt.plot(x,y)
    plt.show()
