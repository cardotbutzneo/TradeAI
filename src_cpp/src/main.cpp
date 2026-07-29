#include "../include/header.h"
#include "../include/log.h"
#include "../include/bourse.h"
#include "../include/load_ressorces.h"
#include "../include/run_simulation.h"
#include <thread>

using namespace std;

int main(int argc, char *argv[]) {
    Logger logger;

    logger.debug("C++_Main", "C++ lancé");

    vector<IndexMap> index_actions(20);
    vector<IndexMap> index_dates(1100);
    int nb_actions = 0, nb_dates = 0;

    std::map<std::string, Action> liste_des_actions;
    vector<long long> liste_des_quantites;

    std::ifstream file_stream;
    std::istream* source = nullptr;

    map<std::string, std::string> args = parse_arguments(argc, argv);

    if (args["mode"] == "train") {
        if (args["input"].empty()) {
            logger.error("Main", "Mode train nécessite un fichier d'entrée");
            return static_cast<int>(ExitCode::INVALIDE_ARG);
        }
        file_stream.open(args["input"]);
        if (!file_stream.is_open()) {
            logger.error("Main", "Fichier introuvable");
            return static_cast<int>(ExitCode::CONFIG_ERROR);
        }
        source = &file_stream;
    } else {
        source = &std::cin;
    }

    auto matrix = read_file(*source, ",", index_actions, index_dates,
                            liste_des_actions, liste_des_quantites, nb_actions, nb_dates);
    if (!matrix) {
        logger.error("Main", "Fichier csv non trouvé ou inexistant");
        cout << "STOP" << endl;
        return static_cast<int>(ExitCode::ENGINE_CRASH);
    }

    Portfolio portefeuille;
    portefeuille.cash = 1000.0f;
    portefeuille.shares_owned.assign(nb_actions, 0);

    string register_client;
    if (!getline(cin, register_client) || register_client != "REGISTER") {
        logger.error("C++ Main", "Impossible de détecter les clients. Arret du programme...");
        return static_cast<int>(ExitCode::ENGINE_CRASH);
    }
    logger.debug("C++ Main", "Lancement de l'enregistrement des clients Python");

    if (!validate_start_signal(logger)) {
        logger.error("Main", "Signal invalide");
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }

    std::thread t(lire_ordres);
    t.detach();

    run_simulation(*matrix, index_actions, index_dates, liste_des_actions,
                   liste_des_quantites, nb_actions, nb_dates, args, portefeuille, logger);

    cout << "STOP" << endl;
    return static_cast<int>(ExitCode::SUCCESS);
}
