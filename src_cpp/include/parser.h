#pragma once

#include "main.h"

std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& index_actions,
                                            std::vector<IndexMap>& index_dates,
                                            std::map<std::string, Action>& liste_des_actions,
                                            std::vector<long long>& liste_des_quantites,
                                            int& nb_actions, int& nb_dates);
std::string trim(const std::string& str);