#include "../include/header.h"
#include "../include/parser.h"
#include "../include/bourse.h"
#include <thread>
#include <mutex>
#include <queue>

using namespace std;

std::queue<std::string> ordre_queue;
std::mutex queue_mutex;

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

int main(int argc, char *argv[]) {

    string mode = "";
    bool fast = false;
    if (argc == 1) {
        cerr << "Erreur pas de mode trouvé.\n" << "Arret du programme..." << endl;
        exit(1);
    }
    else if (argc >= 3) mode = argv[1];

    if (argc == 4 && argv[3] == std::string("--fast")) {
        fast = true;
    }

    cerr << mode << endl;
    
    if (mode != "--prod" && mode != "--train") {
        cerr << "Erreur de parametre : veuillez mettre --train ou --prod" << endl;
        exit(1);
    } 

    vector<IndexMap> index_actions(20); // 20 est suffisant mais on peut aller à 200 actions
    vector<IndexMap> index_dates(1100); // le chiffre peut changer en fonction du nombre de points simulés
    int nb_actions = 0, nb_dates = 0;

    std::map<std::string, Action> liste_des_actions;
    vector<long long> liste_des_quantites;

    std::ifstream file_stream;
    std::istream* source = nullptr;

    if (mode == "--train") {
        file_stream.open(argv[2]);
        if (!file_stream.is_open()) { cerr << "Fichier introuvable\n"; return 1; }
        source = &file_stream;
    } else {
        source = &std::cin; // En mode prod, les données arrivent via stdin
    }

    auto matrix = read_file(*source, ",", index_actions, index_dates,
                         liste_des_actions, liste_des_quantites, nb_actions, nb_dates);/*Récupere l'entierete des actions historique dans un tableau numpy*/
    if (!matrix) {
        cerr << "Fichier csv non trouvé ou inexistant" << endl;
        cout << "STOP" << endl; 
        return -1;
    }

    Portfolio portefeuille;
    portefeuille.cash = 1000.0f;
    portefeuille.shares_owned.assign(nb_actions, 0); /*comme calloc()*/

    string signal;
    getline(cin,signal);
    cerr << "[Debug] Signal : " << signal << endl;
    if (signal != "START"){ cerr << "Signal invalide\n"; return 1; }

    std::thread t(lire_ordres);
    t.detach();

    for (int j = 0; j < matrix->cols; j++) {
        string date_actuelle = index_dates[j].cle;

        // On envoie à Python les prix de TOUTES les actions pour ce jour J
        // Format envoyé : TICK;date;ticker1:prix1:volume1,ticker2:prix2:volume2,... -- on envoie pas le hash ca serait trop lourd
        cout << "TICK;" << date_actuelle << ";";
        for (int i = 0; i < matrix->rows; i++) {
            if (!fast) std::this_thread::sleep_for(std::chrono::milliseconds(100)); // pause de 100ms à tous les ticks 

            float prix = matrix->data[i * matrix->cols + j];
            if (prix != -1.0f) { // Si l'action a un prix valide ce jour-là
                string ticker = get_ticker_name(index_actions, i, nb_actions);
                cout << ticker << ":" << prix << ":" << liste_des_quantites[i] << ",";
            }
        }
        cout << endl; // Le Flush obligatoire pour envoyer à Python

        {
            std::lock_guard<std::mutex> lock(queue_mutex);
            while (!ordre_queue.empty()) {
                std::string ordre = ordre_queue.front();
                ordre_queue.pop();
                cerr << "[Cpp Debug] reçu : " << ordre << endl;

                // Parse client_id et reste
                string client_id, reste;
                stringstream flux(ordre);
                getline(flux, client_id, '|');
                getline(flux, reste);

                if (reste == "PASS" || reste.empty()) {
                    cout << "ACK;" << client_id << ";PASS" << endl;
                    continue;
                }

                stringstream flux_ordres(reste);
                string un_ordre;

                while (getline(flux_ordres, un_ordre, '|')) {
                    if (un_ordre.empty()) continue;

                    stringstream flux_champs(un_ordre);
                    string action, ticker, qte_str;

                    if (!(getline(flux_champs, action,   ';') &&
                        getline(flux_champs, ticker,   ';') &&
                        getline(flux_champs, qte_str,  ';'))) {
                        cerr << "[Cpp Debug] ordre mal formé : " << un_ordre << endl;
                        cout << "ACK;" << client_id << ";REJECT_MALFORMED|";
                        continue;
                    }

                    long long qte = 0;
                    try { qte = stoll(qte_str); }
                    catch (...) {
                        cerr << "[Cpp Debug] quantité invalide : " << qte_str << endl;
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

                    float prix_action = matrix->data[idx_action * matrix->cols + j];

                    if (action == "BUY") {
                        float penality   = liste_des_actions[ticker].return_progressive_malus(qte);
                        float cout_total = prix_action * qte * (1 + FRAIS_COURTAGE_ACHAT + penality);
                        if (verify_buy(portefeuille, prix_action, qte)) {
                            Order new_order{ "", "", OrderType::BUY, (double)prix_action, qte };
                            liste_des_actions[ticker].order_book.process_order(new_order);
                            portefeuille.cash -= cout_total;
                            portefeuille.shares_owned[idx_action] += qte;
                            cout << "ACK;" << client_id << ";OK;" << portefeuille.cash << "|";
                        } else {
                            cout << "ACK;" << client_id << ";REJECT_NO_CASH|";
                        }
                    }
                    else if (action == "SELL") {
                        float penality   = liste_des_actions[ticker].return_progressive_malus(qte);
                        float cout_total = prix_action * qte * (1 - FRAIS_COURTAGE_VENTE - penality);
                        if (verify_sell(portefeuille, qte, idx_action)) {
                            Order new_order{ "", "", OrderType::SELL, (double)prix_action, qte };
                            liste_des_actions[ticker].order_book.process_order(new_order);
                            portefeuille.cash += cout_total;
                            portefeuille.shares_owned[idx_action] -= qte;
                            cout << "ACK;" << client_id << ";OK;" << portefeuille.cash << "|";
                        } else {
                            cout << "ACK;" << client_id << ";REJECT_NO_SHARES|";
                        }
                    }
                    else {
                        cout << "ACK;" << client_id << ";REJECT_UNKNOWN_ACTION|";
                    }
                }
                cout << endl;
            }
        }
    }

    // Fin de la simulation historique
    cout << "STOP" << endl;
    return 0;
}