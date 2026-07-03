#include "../include/header.h"
#include "../include/bourse.h"
#include "../include/book_order.h"

static int obtenir_index(std::vector<IndexMap>& table, int& taille_actuelle, const std::string& texte) {
    for (int i = 0; i < taille_actuelle; i++)
        if (table[i].cle == texte) return table[i].index;

    if (taille_actuelle >= (int)table.size()){
        // on créer un vecteur plus grand
        table.resize(table.size() + 200); // on augmente de 200 à chaque fois pour pas consommer trop de mémoire
    }
    table[taille_actuelle].cle   = texte;
    table[taille_actuelle].index = taille_actuelle;
    return taille_actuelle++;
}

std::string trim(const std::string& str) {
    const std::string whitespace = " \t\n\r\f\v";
    size_t start = str.find_first_not_of(whitespace);
    if (start == std::string::npos) return ""; // Empty or all whitespace
    
    size_t end = str.find_last_not_of(whitespace);
    return str.substr(start, end - start + 1);
}

std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& index_actions,
                                            std::vector<IndexMap>& index_dates,
                                            map<std::string, Action>& liste_des_actions,
                                            vector<long long>& liste_des_quantites,
                                            int& nb_actions, int& nb_dates) {

    // Première passe : collecter tickers et dates
    std::string line, ticker, price_str, date, volume_str, curency, hash;
    line.reserve(256); // réserve 256 octects pour la ligne

    while (getline(file, line)) { // fichier ou stdin
        //line = trim(line);
        istringstream ss(line);
        if (getline(ss, date, sep[0]) &&
            getline(ss, ticker, sep[0]) &&
            getline(ss, price_str, sep[0]) &&
            getline(ss, volume_str, sep[0]) &&
            getline(ss, curency, sep[0]) &&
            getline(ss, hash, sep[0])
        ) {
            obtenir_index(index_actions, nb_actions, ticker);
            obtenir_index(index_dates,   nb_dates,   date);
        }
    }

    auto matrix       = std::make_unique<FinancialNDArray>();
    matrix->rows      = nb_actions;
    matrix->cols      = nb_dates;
    matrix->data.assign(nb_actions * nb_dates, -1.0f);

    // Deuxième passe : remplir la matrice
    file.clear();
    file.seekg(0);
    while (std::getline(file, line)) {
        istringstream ss(line);
        string ticker, price_str, date, volume_str;
        if (getline(ss, date, sep[0]) &&
            getline(ss, ticker, sep[0]) &&
            getline(ss, price_str, sep[0]) &&
            getline(ss, volume_str, sep[0]) &&
            getline(ss, curency, sep[0]) &&
            getline(ss, hash, sep[0])) {
            float price   = std::stof(price_str);
            long long volume = volume_str.empty() ? 0LL : stoll(volume_str);
            int ligne     = obtenir_index(index_actions, nb_actions, ticker);
            int colonne   = obtenir_index(index_dates,   nb_dates,   date);
            matrix->data[ligne * matrix->cols + colonne] = price;
            liste_des_quantites.push_back(volume);

            auto& action = liste_des_actions[ticker];
            action.id = ticker;
            action.last_traded_price = price;
            action.current_volume += volume;

            if (action.total_shares == 0){
                action.total_shares = volume;
            }
        }
    }
    return matrix;
}