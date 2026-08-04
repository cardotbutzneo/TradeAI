/**
 * @file run_simulation.h
 * @brief Main simulation loop: replays the price matrix tick by tick,
 *        broadcasts prices and processes client orders received on stdin
 *        (see src/run_market_simulation.cpp).
 */
#pragma once

#include "header.h"
#include "log.h"
#include "bourse.h"
#include <map>
#include <vector>

/** @brief Blocks reading one line from stdin and checks it equals "START" (the handshake signal expected after REGISTER). */
bool validate_start_signal(Logger& logger);

/**
 * @brief Drives the simulation: for each date column, broadcasts a TICK
 *        line with every stock's price/volume, then drains order_queue and
 *        applies each client order (BUY/SELL) against the matching
 *        FinancialNDArray price and the stock's OrderBook, replying with an
 *        ACK line per order.
 * @param matrix Price matrix (rows = stocks, cols = dates).
 * @param stock_index Ticker -> row index table.
 * @param date_index Date -> column index table (column key used for TICK output).
 * @param stocks[in,out] Per-ticker Action aggregates, including each OrderBook.
 * @param volumes Per-stock volume aligned with matrix rows.
 * @param nb_stocks Number of distinct tickers.
 * @param nb_dates Unused by the loop itself (kept for signature symmetry with get_price_matrix()).
 * @param args Runtime options (notably `args["fast"]`, which shortens the real-time pause between ticks -- see send_ticks -- rather than skipping it: the engine never waits on clients, but always paces itself in real time so they have a chance to keep up).
 * @param clients[in,out] Registered clients whose portfolios are updated as orders execute.
 * @param logger Destination for debug/error tracing.
 */
void run_simulation(const FinancialNDArray& matrix,
                    const std::vector<IndexMap>& stock_index,
                    const std::vector<IndexMap>& date_index,
                    std::map<std::string, Action>& stocks,
                    const std::vector<long long>& volumes,
                    int nb_stocks,
                    int nb_dates,
                    const std::map<std::string, std::string>& args,
                    std::map<std::string, Client>& clients,
                    Logger& logger);
