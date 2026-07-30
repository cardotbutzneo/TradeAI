#pragma once

#include "header.h"
#include <map>
#include <queue>
#include <mutex>

std::map<std::string, std::string> parse_arguments(int argc, char *argv[]);
void lire_ordres();
string get_ticker_name(const vector<IndexMap>& index_actions, int index, int nb_actions);
std::unique_ptr<FinancialNDArray> get_price_matrix(vector<IndexMap>& index_actions, 
                    vector<IndexMap>& index_dates,
                    int& nb_actions, 
                    int& nb_dates,
                    std::map<std::string, Action>& liste_des_actions,
                    vector<long long>& liste_des_quantites,
                    Logger logger,
                    int argc, char *argv[]);

extern std::queue<std::string> ordre_queue;
extern std::mutex queue_mutex;