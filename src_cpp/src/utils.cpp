/**
 * @file utils.cpp
 * @brief CLI parsing, the stdin order-reader thread, client
 *        registration/trade recording and price-matrix loading (see
 *        include/load_ressorces.h).
 */
#include "../include/header.h"
#include "../include/bourse.h"
#include "../include/book_order.h"
#include "../include/log.h"
#include "../include/parser.h"
#include "../include/load_ressorces.h"

#include <thread>
#include <mutex>
#include <queue>
#include <sstream>
#include <iomanip>
//#include <openssl/sha.h>

/** Pending raw order lines received from stdin (see read_orders()); guarded by queue_mutex. */
std::queue<std::string> order_queue;
/** Guards concurrent access to order_queue between the reader thread and the simulation loop. */
std::mutex queue_mutex;

/**
 * @brief Parses `argv` into {"mode", "fast", "input"}.
 * @details `argv[1]` must be "prod" or "train", otherwise the process exits
 *          with ExitCode::INVALIDE_ARG. Remaining args: "--fast" sets
 *          `args["fast"] = "true"`; the first other argument becomes
 *          `args["input"]`.
 */
std::map<std::string, std::string> parse_arguments(int argc, char *argv[]) {
    Logger logger;
    std::map<std::string, std::string> args;

    if (argc < 2) {
        logger.error("C++_Main", "Error: no mode provided.\n Stopping the program...");
        exit(static_cast<int>(ExitCode::INVALIDE_ARG));
    }

    std::string mode = argv[1];
    if (mode != "prod" && mode != "train") {
        logger.error("Main", "Invalid parameter: please provide train or prod");
        exit(static_cast<int>(ExitCode::INVALIDE_ARG));
    }

    args["mode"] = mode;
    args["fast"] = "false";
    args["input"] = "";

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--fast") {
            args["fast"] = "true";
        } else if (args["input"].empty()) {
            args["input"] = arg;
        }
    }

    logger.debug("Main", "Mode: " + args["mode"] + " fast: " + args["fast"]);
    return args;
}

/** @brief Reads lines from stdin until EOF, pushing each onto order_queue under queue_mutex. Meant to run on a dedicated thread (see main.cpp). */
void read_orders() {
    std::string line;
    while (std::getline(std::cin, line)) {
        std::lock_guard<std::mutex> lock(queue_mutex);
        order_queue.push(line);
    }
}

/** @brief Linear-scans `stock_index[0..nb_stocks)` for the entry whose `.index == index`; returns "UNKNOWN" if none matches. */
string get_ticker_name(const vector<IndexMap>& stock_index, int index, int nb_stocks) {
    for (int i = 0; i < nb_stocks; i++) {
        if (stock_index[i].index == index) return stock_index[i].key;
    }
    return "UNKNOWN";
}

/** @brief Creates a Client with "CTO" and "PEA" accounts, each seeded with `initial_cash` and `nb_stocks` zeroed share positions, and inserts it into `clients` keyed by `client_id`. */
void add_new_client(std::map<std::string, Client>& clients,
                    const std::string& client_id,
                    const std::string& client_name,
                    int nb_stocks,
                    float initial_cash) {

    Client new_client;
    new_client.id   = client_id;
    new_client.name = client_name;

    // Create the two default accounts
    for (const std::string account_type : {"CTO", "PEA"}) {
        AccountType account;
        account.name = account_type;
        account.cash = initial_cash;
        account.shares_owned.assign(nb_stocks, 0);
        new_client.portfolios[account_type] = account;
    }

    clients[client_id] = new_client;
}

/**
 * @brief Parses a "REGISTER;id1:cash1|id2:cash2|..." line and registers
 *        each client via add_new_client().
 * @details Entries missing a ':' are skipped; an unparsable cash value
 *          falls back to 1000.0.
 * @return false if `line` does not start with "REGISTER;"; true otherwise.
 */
bool parse_register_line(const std::string& line,
                         std::map<std::string, Client>& clients,
                         int nb_stocks) {

    Logger logger;
    logger.debug("utils-C++", "Ligne recu pour le REGISTER: " + line);
    const std::string prefix = "REGISTER;";
    if (line.rfind(prefix, 0) != 0) return false;

    std::string payload = line.substr(prefix.size());
    std::stringstream clients_stream(payload);
    std::string entry;
    while (std::getline(clients_stream, entry, '|')) {
        if (entry.empty()) continue;

        size_t sep = entry.find(':');
        if (sep == std::string::npos) continue;

        std::string client_id = entry.substr(0, sep);
        float initial_cash = 1000.0f;
        try {
            initial_cash = std::stof(entry.substr(sep + 1));
        } catch (...) {
            initial_cash = 1000.0f;
        }

        //logger.debug("utils-C++", "Client " + )        

        add_new_client(clients, client_id, client_id, nb_stocks, initial_cash);
    }
    return true;
}

/*
std::string generate_transaction_id(const std::string& buyer,
                                    const std::string& seller,
                                    const std::string& ticker,
                                    double price, long long qty) {
    std::ostringstream raw;
    raw << buyer << seller << ticker
        << std::fixed << std::setprecision(2) << price
        << qty << std::time(nullptr);

    std::string input = raw.str();
    unsigned char digest[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const unsigned char*>(input.c_str()),
           input.size(), digest);

    std::ostringstream hex;
    for (int i = 0; i < 16; i++)
        hex << std::hex << std::setw(2) << std::setfill('0') << (int)digest[i];
    return hex.str();
}
*/
/**
 * @brief Records a Trade against `client`'s `account_type` portfolio: adjusts
 *        `shares_owned[stock_idx]` (+qty on BUY, -qty on SELL), applies
 *        `cash_delta` to the account's cash, and appends the Trade to its
 *        trade_history.
 * @note No-op if `account_type` is not one of the client's portfolios.
 * @param cash_delta Signed cash adjustment (negative for BUY, positive for SELL), pre-computed by the caller.
 */
void record_trade(Client& client,
                  const std::string& account_type,  // "CTO" or "PEA"
                  const std::string& ticker,
                  const std::string& action,
                  double price, long long qty,
                  int stock_idx,
                  double cash_delta) {

    auto account_it = client.portfolios.find(account_type);
    if (account_it == client.portfolios.end()) {
        return;  // unknown account
    }

    AccountType& account = account_it->second;

    Trade t;
    t.ticker         = ticker;
    t.price          = price;
    t.quantity       = qty;
    t.timestamp      = std::time(nullptr);
    t.transaction_id = "#"; //generate_transaction_id(
        //client.id, "MARKET", ticker, price, qty
    //);

    if (action == "BUY") {
        t.buyer  = client.id;
        t.seller = "MARKET";
        account.shares_owned[stock_idx] += qty;
    } else {
        t.buyer  = "MARKET";
        t.seller = client.id;
        account.shares_owned[stock_idx] -= qty;
    }
    account.cash += cash_delta;

    account.trade_history.push_back(t);
}

/**
 * @brief Loads the price matrix: from `args["input"]` (CSV file) in "train"
 *        mode, or from stdin in "prod" mode, via read_file().
 * @return The parsed matrix, or nullptr if the input file is missing/empty
 *         (train mode) or the stream yields no data.
 */
std::unique_ptr<FinancialNDArray> get_price_matrix(const std::map<std::string, std::string>& args,
                    vector<IndexMap>& stock_index,
                    vector<IndexMap>& date_index,
                    int& nb_stocks,
                    int& nb_dates,
                    std::map<std::string, Action>& stocks,
                    vector<long long>& volumes,
                    Logger& logger) {

    std::ifstream file_stream;
    std::istream* source = nullptr;

    if (args.at("mode") == "train") {
        if (args.at("input").empty()) {
            logger.error("Main", "Train mode requires an input file");
            return nullptr;
        }
        file_stream.open(args.at("input"));
        if (!file_stream.is_open()) {
            logger.error("Main", "File not found");
            return nullptr;
        }
        source = &file_stream;
    } else {
        source = &std::cin;
    }

    std::unique_ptr<FinancialNDArray> matrix = read_file(*source, ",", stock_index, date_index,
                            stocks, volumes, nb_stocks, nb_dates);
    if (!matrix) {
        logger.error("Main", "CSV file not found or empty");
    }
    return matrix;
}
