from bourse import Stock, Market
from AI import AI
from graphic import Ai_graph

def main():
    list_id = ["FR0001", "FR0002", "US0001", "GE0001"]
    list_price = [100, 95, 80, 100]
    list_quantity = [100, 100, 120, 300]

    actions: list[Stock] = [
        Stock(i, p, q)
        for i, p, q in zip(list_id, list_price, list_quantity)
    ]

    market = Market(
        actions,
        {stock.ISIN_id: [stock.stock_price] for stock in actions}
    )

    ai = AI(wallet=1000, portfolio={}, global_value=0, tolerance=0.20)

    # Initial condition: full investment in first stock
    first_stock = actions[0]
    qty = int(0.3 * ai.wallet // first_stock.stock_price)
    ai.wallet = first_stock.buy(ai.wallet, qty)
    ai.refresh_portfolio(first_stock.ISIN_id, qty, first_stock.stock_price)

    max_time = 1000
    data = []

    for t in range(max_time):
        market.refresh()
        ai.get_information(market)
        data.append([t, ai.global_value])

    ai.print_portfolio(market)
    Ai_graph(data)

if __name__ == "__main__":
    main()