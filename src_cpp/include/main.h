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

#include "bourse.h"
#include "book_order.h"
using namespace std;

constexpr float FRAIS_COURTAGE_ACHAT = 0.001f;
constexpr float FRAIS_COURTAGE_VENTE = 0.001f;
constexpr float ERROR_VALUE          = -1.0f;