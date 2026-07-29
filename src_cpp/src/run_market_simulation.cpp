#include "../include/header.h"
#include "../include/log.h"
#include "../include/bourse.h"
#include "../include/load_ressorces.h"
#include "../include/run_simulation.h"

#include <sstream>
#include <chrono>
#include <thread>
#include <mutex>

bool validate_start_signal(Logger& logger) {
    std::string signal;
    if (!std::getline(std::cin, signal)) {
        logger.error("Main", "Erreur de lecture du signal START");
        return false;
    }
    logger.debug("Main", "Signal : " + signal);
    return signal == "START";
}

static void send_ticks(const FinancialNDArray& matrix,
                       const std::vector<IndexMap>& index_actions,
                       const std::vector<IndexMap>& index_dates,
                       int nb_actions,
                       const std::vector<long long>& liste_des_quantites,
                       int current_col,
                       const std::map<std::string, std::string>& args) {
                        
    const string& date_actuelle = index_dates[current_col].cle;
    cout << "TICK;" << date_actuelle << ";";

    for (int i = 0; i < matrix.rows; i++) {
        if (args.at("fast") != "true")
            std::this_thread::sleep_for(std::chrono::milliseconds(100));

        float prix = matrix.data[i * matrix.cols + current_col];
        if (prix != -1.0f) {
            string ticker = get_ticker_name(index_actions, i, nb_actions);
            cout << ticker << ":" << prix << ":";
            if (i < (int)liste_des_quantites.size()) {
                cout << liste_des_quantites[i];
            } else {
                cout << 0;
            }
            cout << ",";
        }
    }
    cout << endl;
}

static void execute_buy(Portfolio& portefeuille,
                        const string& client_id,
                        int idx_action,
                        std::map<std::string, Action>& liste_des_actions,
                        long long qte,
                        const string& ticker,
                        float prix_action) {
    if (qte <= 0) {
        cout << "ACK;" << client_id << ";REJECT_INVALID_QTY|";
        return;
    }

    float penality = liste_des_actions[ticker].return_progressive_malus(qte);
    float cout_total = prix_action * qte * (1 + FRAIS_COURTAGE_ACHAT + penality);
    if (!verify_buy(portefeuille, prix_action, static_cast<int>(qte))) {
        cout << "ACK;" << client_id << ";REJECT_NO_CASH|";
        return;
    }

    Order new_order{client_id, "", OrderType::BUY, (double)prix_action, qte};
    liste_des_actions[ticker].order_book.process_order(new_order);
    portefeuille.cash -= cout_total;
    portefeuille.shares_owned[idx_action] += qte;
    cout << "ACK;" << client_id << ";OK;" << portefeuille.cash << "|";
}

static void execute_sell(Portfolio& portefeuille,
                         const string& client_id,
                         int idx_action,
                         std::map<std::string, Action>& liste_des_actions,
                         long long qte,
                         const string& ticker,
                         float prix_action) {
    if (qte <= 0) {
        cout << "ACK;" << client_id << ";REJECT_INVALID_QTY|";
        return;
    }

    if (!verify_sell(portefeuille, static_cast<int>(qte), idx_action)) {
        cout << "ACK;" << client_id << ";REJECT_NO_SHARES|";
        return;
    }

    float penality = liste_des_actions[ticker].return_progressive_malus(qte);
    float cout_total = prix_action * qte * (1 - FRAIS_COURTAGE_VENTE - penality);
    Order new_order{"", client_id, OrderType::SELL, (double)prix_action, qte};
    liste_des_actions[ticker].order_book.process_order(new_order);
    portefeuille.cash += cout_total;
    portefeuille.shares_owned[idx_action] -= qte;
    cout << "ACK;" << client_id << ";OK;" << portefeuille.cash << "|";
}

static void process_order_line(const string& ordre,
                               Portfolio& portefeuille,
                               std::map<std::string, Action>& liste_des_actions,
                               const std::vector<IndexMap>& index_actions,
                               int nb_actions,
                               const FinancialNDArray& matrix,
                               int current_col,
                               Logger& logger) {
    string client_id, reste;
    stringstream flux(ordre);
    getline(flux, client_id, '|');
    getline(flux, reste);

    if (reste == "PASS" || reste.empty()) {
        cout << "ACK;" << client_id << ";PASS" << endl;
        return;
    }

    stringstream flux_ordres(reste);
    string un_ordre;
    while (getline(flux_ordres, un_ordre, '|')) {
        if (un_ordre.empty()) continue;

        stringstream flux_champs(un_ordre);
        string action, ticker, qte_str;
        if (!(getline(flux_champs, action, ';') &&
              getline(flux_champs, ticker, ';') &&
              getline(flux_champs, qte_str, ';'))) {
            logger.debug("Main", "[Cpp Debug] ordre mal formé : " + un_ordre);
            cout << "ACK;" << client_id << ";REJECT_MALFORMED|";
            continue;
        }

        long long qte = 0;
        try {
            qte = stoll(qte_str);
        } catch (...) {
            logger.debug("Main", "[Cpp Debug] quantité invalide : " + qte_str);
            cout << "ACK;" << client_id << ";REJECT_INVALID_QTY|";
            continue;
        }

        int idx_action = -1;
        for (int i = 0; i < nb_actions; i++) {
            if (index_actions[i].cle == ticker) {
                idx_action = index_actions[i].index;
                break;
            }
        }
        if (idx_action == -1) {
            cout << "ACK;" << client_id << ";REJECT_UNKNOWN_TICKER|";
            continue;
        }

        if (idx_action < 0 || idx_action >= matrix.rows) {
            cout << "ACK;" << client_id << ";REJECT_UNKNOWN_TICKER|";
            continue;
        }

        float prix_action = matrix.data[idx_action * matrix.cols + current_col];
        if (prix_action == -1.0f) {
            cout << "ACK;" << client_id << ";REJECT_NO_PRICE|";
            continue;
        }

        if (action == "BUY") {
            execute_buy(portefeuille, client_id, idx_action, liste_des_actions, qte, ticker, prix_action);
        } else if (action == "SELL") {
            execute_sell(portefeuille, client_id, idx_action, liste_des_actions, qte, ticker, prix_action);
        } else {
            cout << "ACK;" << client_id << ";REJECT_UNKNOWN_ACTION|";
        }
    }
    cout << endl;
}

void run_simulation(const FinancialNDArray& matrix,
                    const std::vector<IndexMap>& index_actions,
                    const std::vector<IndexMap>& index_dates,
                    std::map<std::string, Action>& liste_des_actions,
                    const std::vector<long long>& liste_des_quantites,
                    int nb_actions,
                    int nb_dates,
                    const std::map<std::string, std::string>& args,
                    Portfolio& portefeuille,
                    Logger& logger) {
    (void)nb_dates;
    for (int j = 0; j < matrix.cols; j++) {
        send_ticks(matrix, index_actions, index_dates, nb_actions, liste_des_quantites, j, args);

        std::lock_guard<std::mutex> lock(queue_mutex);
        while (!ordre_queue.empty()) {
            std::string ordre = ordre_queue.front();
            ordre_queue.pop();
            logger.debug("Main", "[Cpp Debug] reçu : " + ordre);
            process_order_line(ordre, portefeuille, liste_des_actions,
                               index_actions, nb_actions, matrix, j, logger);
        }
    }
}
