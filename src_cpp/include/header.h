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

constexpr float BUY_FEE_RATE  = 0.001f;
constexpr float SELL_FEE_RATE = 0.001f;
constexpr float ERROR_VALUE   = -1.0f;

enum ExitCode : int {
    SUCCESS = 0,
    CONFIG_ERROR = 3,
    PORT_BIND_FAILED = 4,
    ENGINE_CRASH = 5,
    INVALIDE_ARG = 6
};