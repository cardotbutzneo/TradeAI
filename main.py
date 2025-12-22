from bourse import Stock, Market
import AI
from graphic import price_graph

def main():
    actions = [Stock("FR0001",100,100)]
    market = Market(actions,{"FR0001" : []})
    market.history["FR0001"].append(actions[0].stock_price)

    max_time = 10
    market.print_Market()
    for t in range(max_time):
        market.refresh()
        market.print_Market()
    
    price_graph(
    market.history[actions[0].ISIN_id],
    actions[0].ISIN_id
)
        

if __name__ == "__main__":
    main()