/**
 * @file bourse.h
 * @brief Core domain types shared by the market simulation: index lookup
 *        tables, the dense price matrix, client accounts/portfolios, and
 *        the account/price validation helpers.
 */
#pragma once

#include "header.h"
#include "book_order.h"

/** Maps a string key (ticker or date) to its row/column index in FinancialNDArray. */
struct IndexMap {
    std::string key;
    int index = 0;
};

/** Dense row-major matrix of prices: rows = stocks, cols = dates (see FinancialNDArray::data indexing as `row * cols + col`). */
struct FinancialNDArray {
    int rows = 0, cols = 0;
    std::vector<float> data;
};

/** A single brokerage account (e.g. "CTO" or "PEA") belonging to a Client. */
struct AccountType {
    std::string              name;           // "CTO", "PEA"
    float                    cash;
    std::vector<int>         shares_owned;   // indexed by stock index
    std::vector<Trade>       trade_history;
};

/** A registered simulation participant and its portfolios, keyed by account type name. */
struct Client {
    std::string name;
    std::string id;
    std::map<std::string, AccountType> portfolios;  // "CTO" -> AccountType
};

// Declarations
/** @brief Parses a price/volume CSV stream into a FinancialNDArray and populates the index tables (see parser.cpp for the implementation). */
std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& stock_index,
                                            std::vector<IndexMap>& date_index,
                                            std::map<std::string, Action>& stocks,
                                            std::vector<long long>& volumes,
                                            int& nb_stocks, int& nb_dates);
/** @brief Checks that `account` has enough cash to buy `quantity` shares at `amount`, fees included. */
bool  verify_buy(const AccountType&, float, int);
/** @brief Checks that `account` owns at least `quantity` shares of the stock at `stock_idx`. */
bool  verify_sell(const AccountType&, int, int);
/** @brief Returns the matrix price at (stock_line, date_col), or -1 if date_col is before current_sim_col. */
float get_price_safe(const FinancialNDArray&, int, int, int);
/** @brief Arithmetic mean of `arr[0..size)`, or ERROR_VALUE if the array is null/empty. */
float get_average(const float*, int);
