#pragma once

#include "main.h"


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
std::unique_ptr<Portfolio>        init_modele(float cash_init, int nb_actions);
std::unique_ptr<FinancialNDArray> read_file(const std::string&, const std::string&,
                                            std::vector<IndexMap>&, std::vector<IndexMap>&,
                                            int&, int&);
bool  verify_buy(const Portfolio&, float, int);
bool  verify_sell(const Portfolio&, int, int);
float get_price_safe(const FinancialNDArray&, int, int, int);
float get_average(const float*, int);