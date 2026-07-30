#pragma once

#include "header.h"
#include <map>
#include <queue>
#include <mutex>

std::map<std::string, std::string> parse_arguments(int argc, char *argv[]);
void read_orders();
string get_ticker_name(const vector<IndexMap>& stock_index, int index, int nb_stocks);
std::unique_ptr<FinancialNDArray> get_price_matrix(const std::map<std::string, std::string>& args,
                    vector<IndexMap>& stock_index,
                    vector<IndexMap>& date_index,
                    int& nb_stocks,
                    int& nb_dates,
                    std::map<std::string, Action>& stocks,
                    vector<long long>& volumes,
                    Logger& logger);

void add_new_client(std::map<std::string, Client>& clients,
                    const std::string& client_id,
                    const std::string& client_name,
                    int nb_stocks,
                    float initial_cash = 1000.0f);

bool parse_register_line(const std::string& line,
                         std::map<std::string, Client>& clients,
                         int nb_stocks);

void record_trade(Client& client,
                  const std::string& account_type,  // "CTO" or "PEA"
                  const std::string& ticker,
                  const std::string& action,
                  double price, long long qty,
                  int stock_idx,
                  double cash_delta);

extern std::queue<std::string> order_queue;
extern std::mutex queue_mutex;
