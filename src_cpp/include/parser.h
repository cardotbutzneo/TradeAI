/**
 * @file parser.h
 * @brief CSV price-file parsing helpers (see src/parser.cpp).
 */
#pragma once

#include "header.h"
#include "bourse.h"

/**
 * @brief Reads a `date,ticker,price,volume,currency,hash` CSV stream in two
 *        passes: first to discover tickers/dates and size the matrix, then
 *        to fill it and accumulate per-stock volume/price data.
 * @param file Input stream (file or stdin), read from its current position and rewound internally.
 * @param sep Field separator (only its first character is used).
 * @param stock_index[out] Ticker -> row index table, grown as new tickers are seen.
 * @param date_index[out] Date -> column index table, grown as new dates are seen.
 * @param stocks[out] Per-ticker Action aggregates (id, last price, cumulative volume).
 * @param volumes[out] Volume of each parsed row, in file order.
 * @param nb_stocks[out] Number of distinct tickers discovered.
 * @param nb_dates[out] Number of distinct dates discovered.
 * @return The populated price matrix (rows = stocks, cols = dates).
 */
std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& stock_index,
                                            std::vector<IndexMap>& date_index,
                                            std::map<std::string, Action>& stocks,
                                            std::vector<long long>& volumes,
                                            int& nb_stocks, int& nb_dates);
/** @brief Strips leading/trailing whitespace (space, tab, \\n, \\r, \\f, \\v) from `str`. */
std::string trim(const std::string& str);
