#include "../include/main.h"

string get_ticker_name(const vector<IndexMap>& index_actions, int index, int nb_actions) {
    for (int i = 0; i < nb_actions; i++) {
        if (index_actions[i].index == index) return index_actions[i].cle;
    }
    return "UNKNOWN";
}

int main(int argc, char *argv[]) {
    string mode = "";
    if (argc == 1) {
        cerr << "Pas de mode trouvé -- Passage en mode training" << endl;
        argc = 1;
        mode = "--train";
    }
    else if (argc == 2 && argv) mode = argv[1];
    
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
        file_stream.open("../data/historic.csv");
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

    for (int j = 0; j < matrix->cols; j++) {
        string date_actuelle = index_dates[j].cle;

        // On envoie à Python les prix de TOUTES les actions pour ce jour J
        // Format envoyé : TICK;date;ticker1:prix1:volume1,ticker2:prix2:volume2,... -- on envoie pas le hash ca serait trop lourd
        cout << "TICK;" << date_actuelle << ";";
        for (int i = 0; i < matrix->rows; i++) {
            float prix = matrix->data[i * matrix->cols + j];
            if (prix != -1.0f) { // Si l'action a un prix valide ce jour-là
                string ticker = get_ticker_name(index_actions, i, nb_actions);
                cout << ticker << ":" << prix << ":" << liste_des_quantites[i] << ",";
            }
        }
        cout << endl; // Le Flush obligatoire pour envoyer à Python

        // 4. Attente de la décision de Python via l'entrée standard
        string ordre_python;
        string order;
        stringstream ss(order);

        if (getline(cin, ordre_python)) {
            cerr << "[Cpp Debug] reçu : " << ordre_python << endl;

            if (ordre_python == "PASS") continue;

            // Découpe les ordres séparés par '|'
            stringstream flux_ordres(ordre_python);
            string un_ordre;

            while (getline(flux_ordres, un_ordre, '|')) {
                if (un_ordre.empty()) continue;

                // Découpe chaque ordre en champs séparés par ';'
                stringstream flux_champs(un_ordre);
                string action, ticker, qte_str;

                if (!(getline(flux_champs, action, ';') &&
                    getline(flux_champs, ticker,   ';') &&
                    getline(flux_champs, qte_str,  ';'))) {
                    cerr << "[Cpp Debug] ordre mal formé : " << un_ordre << endl;
                    continue;
                }

                long long qte = 0;
                try { qte = stoi(qte_str); }
                catch (...) { cerr << "[Cpp Debug] quantité invalide : " << qte_str << endl; continue; }

                // Recherche de l'action
                int idx_action = -1;
                for (int i = 0; i < nb_actions; i++) {
                    if (index_actions[i].cle == ticker) { idx_action = index_actions[i].index; break; }
                }
                if (idx_action == -1) {
                    cerr << "[Cpp Debug] ticker inconnu : " << ticker << endl;
                    cout << "ACK;REJECT_UNKNOWN_TICKER|";
                    continue;
                }

                float prix_action = matrix->data[idx_action * matrix->cols + j];

                if (action == "BUY") {
                    float penality = liste_des_actions[ticker].return_progressive_malus(qte); // calcule de penalité dans le cas d'une vente/achat trop important
                    float cout_total = prix_action * qte * (1 + FRAIS_COURTAGE_ACHAT + penality);
                    if (verify_buy(portefeuille, prix_action, qte)) {
                        Order new_order{ "", "", OrderType::BUY, (double)prix_action, qte };
                        liste_des_actions[ticker].order_book.process_order(new_order);
                        portefeuille.cash -= cout_total;
                        portefeuille.shares_owned[idx_action] += qte;
                        cout << "ACK;OK;" << portefeuille.cash << "|";
                    } else {
                        cout << "ACK;REJECT_NO_CASH|";
                    }
                }
                else if (action == "SELL") {
                    float penality = liste_des_actions[ticker].return_progressive_malus(qte);
                    float cout_total = prix_action * qte * (1 - FRAIS_COURTAGE_VENTE - penality);
                    if (verify_sell(portefeuille, qte, idx_action)) { // ⚠️ idx_action, pas j
                        Order new_order{ "", "", OrderType::SELL, (double)prix_action, qte };
                        liste_des_actions[ticker].order_book.process_order(new_order);
                        portefeuille.cash += cout_total;
                        portefeuille.shares_owned[idx_action] -= qte;
                        cout << "ACK;OK;" << portefeuille.cash << "|";
                    } else {
                        cout << "ACK;REJECT_NO_SHARES|";
                    }
                }
                else {
                    cerr << "[Cpp Debug] action inconnue : " << action << endl;
                    cout << "ACK;REJECT_UNKNOWN_ACTION|";
                }
            }
            cout << endl;
        }
    }

    // Fin de la simulation historique
    cout << "STOP" << endl;
    return 0;
}