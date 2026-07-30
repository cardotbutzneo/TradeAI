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

    

    if (!validate_start_signal(logger)) {
        logger.error("Main", "Signal invalide");
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }

    std::map<std::string, Client> list_client;
    

    std::thread t(lire_ordres);
    t.detach();

    run_simulation(*matrix, index_actions, index_dates, liste_des_actions,
                   liste_des_quantites, nb_actions, nb_dates, args, portefeuille, logger);

    cout << "STOP" << endl;
    return static_cast<int>(ExitCode::SUCCESS);
}
