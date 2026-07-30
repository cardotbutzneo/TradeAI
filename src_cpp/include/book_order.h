#pragma once

#include "header.h"
#include <cmath>

#define PENALTY_RATE 0.01 // 1% per 10% above the traded volume

/** Standalone entity managing order books. */

enum class OrderType { BUY, SELL };

struct Order {
    std::string buying_client;
    std::string selling_client;
    OrderType side;        // BUY or SELL
    double price;          // Limit price requested
    long long quantity;    // Number of shares requested
};

struct Trade {
    std::string transaction_id;
    std::string ticker;
    std::string buyer;
    std::string seller;
    double      price;
    long long   quantity;
    time_t      timestamp;
};

class OrderBook {
private:
    // Sorted by descending price (highest buy price first)
    std::multimap<double, Order, std::greater<double>> bids;

    // Sorted by ascending price (cheapest sell price first)
    std::multimap<double, Order, std::less<double>> asks;

public:
    long long total_quantity; // total number of shares
    double best_bid = 0.0;
    double best_ask = 0.0;
    std::vector<Trade> trade_history; // history of past trades

    // Master function: adds an order and tries to match it (Matching Engine)
    void process_order(const Order& new_order) {
        if (new_order.side == OrderType::BUY) {
            match_buy_order(new_order);
        } else {
            match_sell_order(new_order);
        }
        update_market_prices();
    }

private:
    long long execute_trade(Order &buyer, Order &seller, double trade_price){
        long long traded_qty = std::min(buyer.quantity, seller.quantity);

        buyer.quantity -= traded_qty;
        seller.quantity -= traded_qty;

        Trade t;
        t.transaction_id = generate_transaction_id(buyer, seller, trade_price);
        t.buyer = buyer.buying_client;
        t.seller = seller.selling_client;
        t.price = trade_price;
        t.quantity = traded_qty;
        t.timestamp = std::time(nullptr);
        trade_history.push_back(t);

        std::cerr << "[TRADE] " << t.buyer << " buys " << traded_qty
                  << " shares from " << t.seller << " at " << trade_price << "\n";

        return traded_qty;
    }

    std::string generate_transaction_id(const Order& buyer, const Order& seller, double price){
        std::ostringstream raw;
        raw << buyer.buying_client << seller.selling_client << std::fixed << std::setprecision(2) << price << std::time(nullptr); // hash
        return raw.str().substr(0, 32);
    }

    void match_buy_order(Order buy_order) {
        // While there are sellers and the buy price covers the cheapest ask
        while (!OrderBook::asks.empty() && buy_order.price >= asks.begin()->first && buy_order.quantity > 0) {
            auto best_ask_it = asks.begin();
            Order& sell_order = best_ask_it->second;

            // Compute the traded quantity (the minimum of the two)
            long long traded_qty = std::min(buy_order.quantity, sell_order.quantity);

            // HERE: the trade for 'traded_qty' shares happens at 'sell_order.price'!

            buy_order.quantity -= traded_qty;
            sell_order.quantity -= traded_qty;

            if (sell_order.quantity == 0) {
                OrderBook::asks.erase(best_ask_it); // The sell order is fully executed
            }
        }
        // If some quantity remains unbought, keep the remainder queued in the book
        if (buy_order.quantity > 0) {
           OrderBook::bids.insert({buy_order.price, buy_order});
        }
    }

    void match_sell_order(Order sell_order) {
    while (!bids.empty() && sell_order.price <= bids.begin()->first && sell_order.quantity > 0) {
        auto best_bid_it = bids.begin();
        Order& buy_order = best_bid_it->second;

        long long traded_qty = std::min(sell_order.quantity, buy_order.quantity);

        sell_order.quantity -= traded_qty;
        buy_order.quantity  -= traded_qty;

        if (buy_order.quantity == 0) {
            bids.erase(best_bid_it);
        }
    }

    if (sell_order.quantity > 0) {
        asks.insert({sell_order.price, sell_order});
    }
}

    void update_market_prices() {
        if (!OrderBook::bids.empty()) best_bid = OrderBook::bids.begin()->first;
        if (!OrderBook::asks.empty()) best_ask = OrderBook::asks.begin()->first;
    }

    public:
        void print_orderbook(const std::string& ticker) const {
            std::cout << "\n=== ORDER BOOK " << ticker << " ===\n";
            std::cout << "ASKS (sellers):\n";
            for (auto& [price, order] : asks)
                std::cout << "  SELL;" << ticker << ";" << order.quantity
                        << ";" << price << ";" << order.selling_client << "\n";

            std::cout << "BIDS (buyers):\n";
            for (auto& [price, order] : bids)
                std::cout << "  BUY;" << ticker << ";" << order.quantity
                        << ";" << price << ";" << order.buying_client << "\n";
        }

        void print_trade_history(const std::string& ticker) const {
            std::cout << "\n=== TRADE HISTORY " << ticker << " ===\n";
            for (auto& t : trade_history)
                std::cout << "  " << t.buyer << " <- " << t.quantity
                        << " shares <- " << t.seller
                        << " at " << t.price << "\n";
        }
};

class Action {
public:
    std::string id;               // stock name
    long long total_shares;       // total number of shares issued by the company
    double last_traded_price;     // last price at which a trade actually occurred
    long long current_volume;     // cumulative volume traded today

    OrderBook order_book;         // order book for this stock

    float compute_penalty(long long x) {
        if (current_volume == 0.0f) return 0.0f;
        long long threshold = 0.1 * current_volume; // 10% of total traded volume for now
        if (threshold <= 0) return 0.0f;
        double excess           = static_cast<double>(x - threshold);
        double penalty_fraction = excess / threshold; // ratio above the threshold
        return static_cast<float>(PENALTY_RATE * penalty_fraction);
    }
};
