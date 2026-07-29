#include "../include/header.h"
#include "../include/bourse.h"
#include "../include/log.h"

#include <thread>
#include <mutex>
#include <queue>

std::queue<std::string> ordre_queue;
std::mutex queue_mutex;

std::map<std::string, std::string> parse_arguments(int argc, char *argv[]) {
    Logger logger;
    std::map<std::string, std::string> args;

    if (argc < 2) {
        logger.error("C++_Main", "Erreur pas de mode trouvé.\n Arret du programme...");
        exit(static_cast<int>(ExitCode::INVALIDE_ARG));
    }

    std::string mode = argv[1];
    if (mode != "prod" && mode != "train") {
        logger.error("Main", "Erreur de parametre : veuillez mettre train ou prod");
        exit(static_cast<int>(ExitCode::INVALIDE_ARG));
    }

    args["mode"] = mode;
    args["fast"] = "false";
    args["input"] = "";

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--fast") {
            args["fast"] = "true";
        } else if (args["input"].empty()) {
            args["input"] = arg;
        }
    }

    logger.debug("Main", "Mode: " + args["mode"] + " fast: " + args["fast"]);
    return args;
}

void lire_ordres() {
    std::string ligne;
    while (std::getline(std::cin, ligne)) {
        std::lock_guard<std::mutex> lock(queue_mutex);
        ordre_queue.push(ligne);
    }
}

string get_ticker_name(const vector<IndexMap>& index_actions, int index, int nb_actions) {
    for (int i = 0; i < nb_actions; i++) {
        if (index_actions[i].index == index) return index_actions[i].cle;
    }
    return "UNKNOWN";
}