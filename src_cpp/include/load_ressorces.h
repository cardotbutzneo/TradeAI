#pragma once

#include "header.h"
#include <map>
#include <queue>
#include <mutex>

std::map<std::string, std::string> parse_arguments(int argc, char *argv[]);
void lire_ordres();
string get_ticker_name(const vector<IndexMap>& index_actions, int index, int nb_actions);

extern std::queue<std::string> ordre_queue;
extern std::mutex queue_mutex;