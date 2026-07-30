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

/** Fee rate applied to every BUY order, expressed as a fraction of the notional (0.001 = 0.1%). */
constexpr float BUY_FEE_RATE  = 0.001f;
/** Fee rate applied to every SELL order, expressed as a fraction of the notional (0.001 = 0.1%). */
constexpr float SELL_FEE_RATE = 0.001f;
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