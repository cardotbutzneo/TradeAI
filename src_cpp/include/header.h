/**
 * @file header.h
 * @brief Common includes, global constants and process exit codes shared by
 *        every translation unit of the C++ market-simulation engine.
 */
#pragma once
#include <array>
#include <functional>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>
#include <map>
using namespace std;

/**
 * French flat tax (PFU) rate on sale proceeds, expressed as a fraction of the
 * notional (0.302 = 30.2%). Applied on SELL only, never on BUY. Hardcoded:
 * unlike the broker fees below, this isn't expected to change often. Mirror
 * of FLAT_TAX_RATE in src_python/utils/utils.py -- Python is the single
 * source of truth for the *broker* fees (settings.json), but this tax rate
 * is deliberately duplicated in both places since it isn't meant to move.
 */
constexpr float FLAT_TAX_RATE = 0.302f;
/**
 * Broker fee rate applied to every BUY/SELL order, expressed as a fraction of
 * the notional. Configurable via config/settings.json ("broker-fees"); Python
 * is the single source of truth and passes the effective values to this
 * process via --buy-fee/--sell-fee CLI args (see parse_arguments in
 * utils.cpp) so the C++ engine never needs its own JSON parser. Defaults
 * below match settings.json's defaults and only apply if the flags are
 * omitted (e.g. manual CLI runs).
 */
extern float BROKER_BUY_FEE;
/** @copydoc BROKER_BUY_FEE */
extern float BROKER_SELL_FEE;
/** Sentinel returned by price/average helpers when no valid value is available. */
constexpr float ERROR_VALUE   = -1.0f;

/**
 * @brief Process exit codes returned by the C++ engine (`main`), consumed by
 *        the Python orchestrator to distinguish failure modes.
 */
enum ExitCode : int {
    SUCCESS = 0,           ///< Simulation ran and terminated normally.
    CONFIG_ERROR = 3,      ///< Invalid or missing configuration (e.g. price matrix could not be built).
    PORT_BIND_FAILED = 4,  ///< Reserved: communication channel could not be established.
    ENGINE_CRASH = 5,      ///< Reserved: unrecoverable internal error.
    INVALIDE_ARG = 6       ///< Invalid CLI argument or malformed handshake signal (REGISTER/START).
};