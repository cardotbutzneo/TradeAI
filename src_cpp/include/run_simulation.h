#pragma once

#include "header.h"
#include "log.h"
#include "bourse.h"
#include <map>
#include <vector>

bool validate_start_signal(Logger& logger);

void run_simulation(const FinancialNDArray& matrix,
                    const std::vector<IndexMap>& index_actions,
                    const std::vector<IndexMap>& index_dates,
                    std::map<std::string, Action>& liste_des_actions,
                    const std::vector<long long>& liste_des_quantites,
                    int nb_actions,
                    int nb_dates,
                    const std::map<std::string, std::string>& args,
                    Portfolio& portefeuille,
                    Logger& logger);

