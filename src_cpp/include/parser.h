#pragma once

#include "header.h"
#include "bourse.h"

std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& stock_index,
                                            std::vector<IndexMap>& date_index,
                                            std::map<std::string, Action>& stocks,
                                            std::vector<long long>& volumes,
                                            int& nb_stocks, int& nb_dates);
std::string trim(const std::string& str);
