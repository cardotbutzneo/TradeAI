#pragma once

#include "header.h"
#include "book_order.h"

struct IndexMap {
    std::string key;
    int index = 0;
};

struct FinancialNDArray {
    int rows = 0, cols = 0;
    std::vector<float> data;
};

struct AccountType {
    std::string              name;           // "CTO", "PEA"
    float                    cash;
    std::vector<int>         shares_owned;   // indexed by stock index
    std::vector<Trade>       trade_history;
};

struct Client {
    std::string name;
    std::string id;
    std::map<std::string, AccountType> portfolios;  // "CTO" -> AccountType
};

// Declarations
std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& stock_index,
                                            std::vector<IndexMap>& date_index,
                                            std::map<std::string, Action>& stocks,
                                            std::vector<long long>& volumes,
                                            int& nb_stocks, int& nb_dates);
bool  verify_buy(const AccountType&, float, int);
bool  verify_sell(const AccountType&, int, int);
float get_price_safe(const FinancialNDArray&, int, int, int);
float get_average(const float*, int);
