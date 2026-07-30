#include "../include/header.h"
#include "../include/log.h"
#include "../include/bourse.h"
#include "../include/load_ressorces.h"
#include "../include/run_simulation.h"

#include <sstream>
#include <chrono>
#include <thread>
#include <mutex>

// Default account used for every order until multi-account routing (CTO/PEA) is wired up client-side.
static const std::string DEFAULT_ACCOUNT = "CTO";

bool validate_start_signal(Logger& logger) {
    std::string signal;
    if (!std::getline(std::cin, signal)) {
        logger.error("Main", "Error reading the START signal");
        return false;
    }
    logger.debug("Main", "Signal: " + signal);
    return signal == "START";
}

static void send_ticks(const FinancialNDArray& matrix,
                       const std::vector<IndexMap>& stock_index,
                       const std::vector<IndexMap>& date_index,
                       int nb_stocks,
                       const std::vector<long long>& volumes,
                       int current_col,
                       const std::map<std::string, std::string>& args) {

    const string& current_date = date_index[current_col].key;
    cout << "TICK;" << current_date << ";";

    for (int i = 0; i < matrix.rows; i++) {
        if (args.at("fast") != "true")
            std::this_thread::sleep_for(std::chrono::milliseconds(100));

        float price = matrix.data[i * matrix.cols + current_col];
        if (price != -1.0f) {
            string ticker = get_ticker_name(stock_index, i, nb_stocks);
            cout << ticker << ":" << price << ":";
            if (i < (int)volumes.size()) {
                cout << volumes[i];
            } else {
                cout << 0;
            }
            cout << ",";
        }
    }
    cout << endl;
}

static void execute_buy(Client& client,
                        int stock_idx,
                        std::map<std::string, Action>& stocks,
                        long long qty,
                        const string& ticker,
                        float stock_price) {
    if (qty <= 0) {
        cout << "ACK;" << client.id << ";REJECT_INVALID_QTY|";
        return;
    }

    AccountType& account = client.portfolios[DEFAULT_ACCOUNT];

    float penalty = stocks[ticker].compute_penalty(qty);
    float total_cost = stock_price * qty * (1 + BUY_FEE_RATE + penalty);
    if (!verify_buy(account, stock_price, static_cast<int>(qty))) {
        cout << "ACK;" << client.id << ";REJECT_NO_CASH|";
        return;
    }

    Order new_order{client.id, "", OrderType::BUY, (double)stock_price, qty};
    stocks[ticker].order_book.process_order(new_order);
    record_trade(client, DEFAULT_ACCOUNT, ticker, "BUY", stock_price, qty, stock_idx, -total_cost);
    cout << "ACK;" << client.id << ";OK;" << account.cash << "|";
}

static void execute_sell(Client& client,
                         int stock_idx,
                         std::map<std::string, Action>& stocks,
                         long long qty,
                         const string& ticker,
                         float stock_price) {
    if (qty <= 0) {
        cout << "ACK;" << client.id << ";REJECT_INVALID_QTY|";
        return;
    }

    AccountType& account = client.portfolios[DEFAULT_ACCOUNT];

    if (!verify_sell(account, static_cast<int>(qty), stock_idx)) {
        cout << "ACK;" << client.id << ";REJECT_NO_SHARES|";
        return;
    }

    float penalty = stocks[ticker].compute_penalty(qty);
    float total_proceeds = stock_price * qty * (1 - SELL_FEE_RATE - penalty);
    Order new_order{"", client.id, OrderType::SELL, (double)stock_price, qty};
    stocks[ticker].order_book.process_order(new_order);
    record_trade(client, DEFAULT_ACCOUNT, ticker, "SELL", stock_price, qty, stock_idx, total_proceeds);
    cout << "ACK;" << client.id << ";OK;" << account.cash << "|";
}

static void process_order_line(const string& order_line,
                               std::map<std::string, Client>& clients,
                               std::map<std::string, Action>& stocks,
                               const std::vector<IndexMap>& stock_index,
                               int nb_stocks,
                               const FinancialNDArray& matrix,
                               int current_col,
                               Logger& logger) {
    string client_id, remaining;
    stringstream stream(order_line);
    getline(stream, client_id, '|');
    getline(stream, remaining);

    auto client_it = clients.find(client_id);
    if (client_it == clients.end()) {
        cout << "ACK;" << client_id << ";REJECT_UNKNOWN_CLIENT" << endl;
        return;
    }
    Client& client = client_it->second;

    if (remaining == "PASS" || remaining.empty()) {
        cout << "ACK;" << client_id << ";PASS" << endl;
        return;
    }

    stringstream orders_stream(remaining);
    string single_order;
    while (getline(orders_stream, single_order, '|')) {
        if (single_order.empty()) continue;

        stringstream fields_stream(single_order);
        string action, ticker, qty_str;
        if (!(getline(fields_stream, action, ';') &&
              getline(fields_stream, ticker, ';') &&
              getline(fields_stream, qty_str, ';'))) {
            logger.debug("Main", "[Cpp Debug] malformed order: " + single_order);
            cout << "ACK;" << client_id << ";REJECT_MALFORMED|";
            continue;
        }

        long long qty = 0;
        try {
            qty = stoll(qty_str);
        } catch (...) {
            logger.debug("Main", "[Cpp Debug] invalid quantity: " + qty_str);
            cout << "ACK;" << client_id << ";REJECT_INVALID_QTY|";
            continue;
        }

        int stock_idx = -1;
        for (int i = 0; i < nb_stocks; i++) {
            if (stock_index[i].key == ticker) {
                stock_idx = stock_index[i].index;
                break;
            }
        }
        if (stock_idx == -1) {
            cout << "ACK;" << client_id << ";REJECT_UNKNOWN_TICKER|";
            continue;
        }

        if (stock_idx < 0 || stock_idx >= matrix.rows) {
            cout << "ACK;" << client_id << ";REJECT_UNKNOWN_TICKER|";
            continue;
        }

        float stock_price = matrix.data[stock_idx * matrix.cols + current_col];
        if (stock_price == -1.0f) {
            cout << "ACK;" << client_id << ";REJECT_NO_PRICE|";
            continue;
        }

        if (action == "BUY") {
            execute_buy(client, stock_idx, stocks, qty, ticker, stock_price);
        } else if (action == "SELL") {
            execute_sell(client, stock_idx, stocks, qty, ticker, stock_price);
        } else {
            cout << "ACK;" << client_id << ";REJECT_UNKNOWN_ACTION|";
        }
    }
    cout << endl;
}

void run_simulation(const FinancialNDArray& matrix,
                    const std::vector<IndexMap>& stock_index,
                    const std::vector<IndexMap>& date_index,
                    std::map<std::string, Action>& stocks,
                    const std::vector<long long>& volumes,
                    int nb_stocks,
                    int nb_dates,
                    const std::map<std::string, std::string>& args,
                    std::map<std::string, Client>& clients,
                    Logger& logger) {
    (void)nb_dates;
    for (int j = 0; j < matrix.cols; j++) {
        send_ticks(matrix, stock_index, date_index, nb_stocks, volumes, j, args);

        std::lock_guard<std::mutex> lock(queue_mutex);
        while (!order_queue.empty()) {
            std::string order_line = order_queue.front();
            order_queue.pop();
            logger.debug("Main", "[Cpp Debug] received: " + order_line);
            process_order_line(order_line, clients, stocks,
                               stock_index, nb_stocks, matrix, j, logger);
        }
    }
}
