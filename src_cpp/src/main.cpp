#include "../include/main.h"

string get_ticker_name(const vector<IndexMap>& index_actions, int index, int nb_actions) {
    for (int i = 0; i < nb_actions; i++) {
        if (index_actions[i].index == index) return index_actions[i].cle;
    }
    return "UNKNOWN";
}

int main() {
    vector<IndexMap> index_actions(200);
    vector<IndexMap> index_dates(500);
    int nb_actions = 0, nb_dates = 0;

    string filepath = "../data/historic.csv";
    auto matrix = read_file(filepath, ",", index_actions, index_dates, nb_actions, nb_dates); /*Récupere l'entierete des actions historique dans un tableau numpy*/
    if (!matrix) {
        cerr << "Fichier csv non trouvé ou inexistant" << endl;
        cout << "STOP" << endl; 
        return -1;
    }

    Portfolio portefeuille;
    portefeuille.cash = 10000.0f;
    portefeuille.shares_owned.assign(nb_actions, 0); /*comme calloc()*/

    for (int j = 0; j < matrix->cols; j++) {
        string date_actuelle = index_dates[j].cle;

        // On envoie à Python les prix de TOUTES les actions pour ce jour J
        // Format envoyé : TICK;date;ticker1:prix1,ticker2:prix2,...
        cout << "TICK;" << date_actuelle << ";";
        for (int i = 0; i < matrix->rows; i++) {
            float prix = matrix->data[i * matrix->cols + j];
            if (prix != -1.0f) { // Si l'action a un prix valide ce jour-là
                cout << get_ticker_name(index_actions, i, nb_actions) << ":" << prix << ",";
            }
        }
        cout << endl; // Le Flush obligatoire pour envoyer à Python

        // 4. Attente de la décision de Python via l'entrée standard
        string ordre_python;
        if (getline(cin, ordre_python)) {
            if (ordre_python == "PASS") {
                continue; // Rien à faire, on passe au jour suivant
            }
            
            // Exemple d'analyse d'ordre basique : "BUY;AAPL;10"
            stringstream ss(ordre_python);
            string action, ticker, qte_str;
            if (getline(ss, action, ';') && getline(ss, ticker, ';') && getline(ss, qte_str, ';')) {
                int qte = stoi(qte_str);
                
                // On cherche l'index de l'action demandée par Python
                int idx_action = -1;
                for (int i = 0; i < nb_actions; i++) {
                    if (index_actions[i].cle == ticker) { idx_action = index_actions[i].index; break; }
                }

                if (idx_action != -1) {
                    float prix_action = matrix->data[idx_action * matrix->cols + j];
                    
                    if (action == "BUY") {
                        float cout = prix_action * qte * (1 + FRAIS_COURTAGE_ACHAT);
                        if (verify_buy(portefeuille, prix_action, qte)) {
                            portefeuille.cash -= cout;
                            portefeuille.shares_owned[idx_action] += qte;
                            std::cout << "ACK;OK;" << portefeuille.cash << std::endl;
                        } else {
                            // Refusé par la banque
                            std::cout << "ACK;REJECT_NO_CASH" << std::endl;
                        }
                    } 
                    else if (action == "SELL") {
                        if (verify_sell(portefeuille, qte, j)) {
                            portefeuille.cash += prix_action * qte * (1 - FRAIS_COURTAGE_VENTE);
                            portefeuille.shares_owned[idx_action] -= qte;
                            std::cout << "ACK;OK;" << portefeuille.cash << std::endl;
                        }
                        } else {
                            // Refusé par la banque
                            std::cout << "ACK;REJECT_NO_CASH" << std::endl;
                    }
                }
            }
        }
    }

    // Fin de la simulation historique
    cout << "STOP" << endl;
    return 0;
}