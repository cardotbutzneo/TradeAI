from bourse import Stock, Market
#import AI
from graphic import price_graph

def main():
    list_id = ["FR0001", "FR0002","US0001","GE0001"]
    list_price = [100, 95,80,100]
    list_quantity = [100, 100,120,300]

    actions = [
        Stock(i, p, q)
        for i, p, q in zip(list_id, list_price, list_quantity)
    ]

    market = Market(
        actions,
        {stock.ISIN_id: [stock.stock_price] for stock in actions}
    )

    max_time = 1000

    for _ in range(max_time):
        market.refresh()

    price_lists = [market.history[i] for i in list_id]
    price_graph(price_lists, list_id)

        

if __name__ == "__main__":
    main()