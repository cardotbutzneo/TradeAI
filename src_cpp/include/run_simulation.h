#pragma once

#include "header.h"
#include "log.h"
#include "bourse.h"
#include <map>
#include <vector>

bool validate_start_signal(Logger& logger);

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
