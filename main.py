import numpy as np
from bourse import Stock, Market
from AI import AI
from graphic import price_graph,Ai_graph

def main():
    list_id = ["FR0001", "FR0002","US0001","GE0001"]
    list_price = [100, 95,80,100]
    list_quantity = [100, 100,120,300]

    actions = [
        Stock(i, p, q)
        for i, p, q in zip(list_id, list_price, list_quantity)
    ]
    actions : list[Stock]

    market = Market(
        actions,
        {stock.ISIN_id: [stock.stock_price] for stock in actions}
    )

    ai = AI(1000,{},0,0.02)

    min  = actions[0]
    min : Stock
    for stk in actions:
        if stk.stock_price < min.stock_price:
            min = stk

    ai.wallet = min.buy(ai.wallet,ai.wallet//min.stock_price)
    ai.portfolio[min.ISIN_id] = ai.wallet//min.stock_price
    ai.print_portfolio()

    max_time = 100
    data = []

    for t in range(max_time):
        market.refresh()
        ai.get_information(market)
        ai.print_portfolio()
        data.append([t,ai.wallet])

    price_lists = [market.history[i] for i in list_id]
    price_graph(price_lists, list_id)
    Ai_graph(data)

if __name__ == "__main__":
    main()