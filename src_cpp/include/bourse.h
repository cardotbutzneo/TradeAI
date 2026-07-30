#pragma once

#include "header.h"
#include "book_order.h"

struct IndexMap {
    std::string cle;
    int index = 0;
};

struct FinancialNDArray {
    int rows = 0, cols = 0;
    std::vector<float> data;
};

struct AccountType {
    std::string              name;           // "CTO", "PEA"
    float                    cash;
    std::vector<int>         shares_owned;   // par index d'action
    std::vector<Trade>       trade_history;
};

struct Client {
    std::string name;
    std::string id;
    std::map<std::string, AccountType> portfolios;  // "CTO" → AccountType
};

// Déclarations
std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& index_actions,
                                            std::vector<IndexMap>& index_dates,
                                            std::map<std::string, Action>& liste_des_actions,
                                            std::vector<long long>& liste_des_quantites,
                                            int& nb_actions, int& nb_dates);
bool  verify_buy(const Portfolio&, float, int);
bool  verify_sell(const Portfolio&, int, int);
float get_price_safe(const FinancialNDArray&, int, int, int);
float get_average(const float*, int);