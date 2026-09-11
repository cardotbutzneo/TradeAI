/**
 * @file main.cpp
 * @brief Engine entry point. Orchestrates the startup handshake with the
 *        Python side over stdin/stdout: load prices -> REGISTER clients ->
 *        START -> run the tick-by-tick simulation.
 */
#include "../include/header.h"
#include "../include/log.h"
#include "../include/bourse.h"
#include "../include/load_ressorces.h"
#include "../include/run_simulation.h"
#include <thread>

using namespace std;

/**
 * @brief Program entry point.
 *
 * Sequence: parse CLI args -> build the price matrix (get_price_matrix) ->
 * read and parse the "REGISTER;..." line (parse_register_line) -> reply
 * "REGISTER;OK" -> wait for "START" (validate_start_signal) -> spawn the
 * stdin order-reader thread (read_orders) -> run the simulation
 * (run_simulation) -> print "STOP".
 * @return An ExitCode value.
 */
int main(int argc, char *argv[]) {
    Logger logger;

    logger.debug(__FILE__, __func__, "C++ started");

    std::map<std::string, std::string> args = parse_arguments(argc, argv);

    vector<IndexMap> stock_index(20);
    vector<IndexMap> date_index(1100);
    int nb_stocks = 0, nb_dates = 0;

    std::map<std::string, Action> stocks;
    vector<long long> volumes;

    std::unique_ptr<FinancialNDArray> matrix = get_price_matrix(
        args, stock_index, date_index, nb_stocks, nb_dates, stocks, volumes, logger);
    if (!matrix) {
        logger.error(__FILE__, __func__, "Could not build the price matrix");
        return static_cast<int>(ExitCode::CONFIG_ERROR);
    }
    
    std::string register_line;
    if (!std::getline(std::cin, register_line)) {
        logger.error(__FILE__, __func__, "Error reading the REGISTER signal");
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }

    std::map<std::string, Client> clients;
    if (!parse_register_line(register_line, clients, nb_stocks) || clients.empty()) {
        logger.error(__FILE__, __func__, "Invalid REGISTER signal: " + register_line);
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }
    logger.debug(__FILE__, __func__, "Registered " + std::to_string(clients.size()) + " client(s)");
    cout << "REGISTER;OK" << endl;

    if (!validate_start_signal(logger)) {
        logger.error(__FILE__, __func__, "Invalid signal");
        return static_cast<int>(ExitCode::INVALIDE_ARG);
    }

    std::thread t(read_orders);
    t.detach();

    run_simulation(*matrix, stock_index, date_index, stocks,
                   volumes, nb_stocks, nb_dates, args, clients, logger);

    cout << "STOP" << endl;
    return static_cast<int>(ExitCode::SUCCESS);
}
