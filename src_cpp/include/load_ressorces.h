/**
 * @file load_ressorces.h
 * @brief CLI argument parsing, price-matrix loading, client registration
 *        and the thread-safe order queue shared with the stdin reader
 *        thread (see src/utils.cpp).
 */
#pragma once

#include "header.h"
#include <map>
#include <queue>
#include <mutex>

/**
 * @brief Parses CLI arguments into an {mode, fast, input} map.
 * @param argv[1] Required: "prod" or "train"; exits the process (INVALIDE_ARG) if missing/invalid.
 * @param argv[2..] Optional: "--fast" (disables per-tick sleep) and an input file path (train mode).
 */
std::map<std::string, std::string> parse_arguments(int argc, char *argv[]);
/** @brief Blocking loop: reads lines from stdin and pushes them onto order_queue (guarded by queue_mutex). Intended to run on its own thread. */
void read_orders();
/** @brief Reverse lookup of a ticker name from its row index; returns "UNKNOWN" if not found. */
string get_ticker_name(const vector<IndexMap>& stock_index, int index, int nb_stocks);
/** @brief Loads the price matrix: from the `input` file in "train" mode, or from stdin in "prod" mode (see read_file()). Returns nullptr on failure. */
std::unique_ptr<FinancialNDArray> get_price_matrix(const std::map<std::string, std::string>& args,
                    vector<IndexMap>& stock_index,
                    vector<IndexMap>& date_index,
                    int& nb_stocks,
                    int& nb_dates,
                    std::map<std::string, Action>& stocks,
                    vector<long long>& volumes,
                    Logger& logger);

/** @brief Registers a new Client with default "CTO" and "PEA" accounts, each seeded with `initial_cash` and zeroed share positions. */
void add_new_client(std::map<std::string, Client>& clients,
                    const std::string& client_id,
                    const std::string& client_name,
                    int nb_stocks,
                    float initial_cash = 1000.0f);

/**
 * @brief Parses a "REGISTER;id1:cash1|id2:cash2|..." handshake line and
 *        registers each client via add_new_client().
 * @return false if `line` does not start with "REGISTER;"; true otherwise
 *         (individual malformed entries are skipped, not treated as failure).
 */
bool parse_register_line(const std::string& line,
                         std::map<std::string, Client>& clients,
                         int nb_stocks);

/** @brief Appends a Trade to `account_type`'s history, updates the client's share position (+qty on BUY, -qty on SELL) and applies `cash_delta` to its cash balance. No-op if `account_type` is unknown. */
void record_trade(Client& client,
                  const std::string& account_type,  // "CTO" or "PEA"
                  const std::string& ticker,
                  const std::string& action,
                  double price, long long qty,
                  int stock_idx,
                  double cash_delta);

/** Pending raw order lines received from stdin, produced by read_orders() and consumed by run_simulation(). */
extern std::queue<std::string> order_queue;
/** Guards concurrent access to order_queue between the reader thread and the simulation loop. */
extern std::mutex queue_mutex;
