#include "../include/header.h"
#include "../include/log.h"
#include "../include/bourse.h"
#include "../include/load_ressorces.h"
#include "../include/run_simulation.h"
#include <thread>

using namespace std;

int main(int argc, char *argv[]) {
    Logger logger;

    logger.debug("C++ Main", "C++ started");

    std::map<std::string, std::string> args = parse_arguments(argc, argv);

    vector<IndexMap> stock_index(20);
    vector<IndexMap> date_index(1100);
    int nb_stocks = 0, nb_dates = 0;

    std::map<std::string, Action> stocks;
    vector<long long> volumes;

    std::unique_ptr<FinancialNDArray> matrix = get_price_matrix(
        args, stock_index, date_index, nb_stocks, nb_dates, stocks, volumes, logger);
    if (!matrix) {
        logger.error("C++ Main", "Could not build the price matrix");
        return static_cast<int>(ExitCode::CONFIG_ERROR);
    }
    
    std::string register_line;
    if (!std::getline(std::cin, register_line)) {
        logger.error("C++ Main", "Error reading the REGISTER signal");
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }

    std::map<std::string, Client> clients;
    if (!parse_register_line(register_line, clients, nb_stocks) || clients.empty()) {
        logger.error("C++ Main", "Invalid REGISTER signal: " + register_line);
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }
    logger.debug("C++ Main", "Registered " + std::to_string(clients.size()) + " client(s)");
    cout << "REGISTER;OK" << endl;

    if (!validate_start_signal(logger)) {
        logger.error("Main", "Invalid signal");
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }

    std::thread t(read_orders);
    t.detach();

    run_simulation(*matrix, stock_index, date_index, stocks,
                   volumes, nb_stocks, nb_dates, args, clients, logger);

    cout << "STOP" << endl;
    return static_cast<int>(ExitCode::SUCCESS);
}
