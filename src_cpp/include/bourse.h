#pragma once

#include "main.h"
#include "book_order.h"

struct IndexMap {
    std::string cle;
    int index = 0;
};

struct Portfolio {
    float cash        = 0.0f;
    float total_value = 0.0f;
    std::vector<int> shares_owned;
};

struct FinancialNDArray {
    int rows = 0, cols = 0;
    std::vector<float> data;
};


// Déclarations
std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& index_actions,
                                            std::vector<IndexMap>& index_dates,
                                            std::map<std::string, Action>& liste_des_actions,
                                            int& nb_actions, int& nb_dates);
bool  verify_buy(const Portfolio&, float, int);
bool  verify_sell(const Portfolio&, int, int);
float get_price_safe(const FinancialNDArray&, int, int, int);
float get_average(const float*, int);