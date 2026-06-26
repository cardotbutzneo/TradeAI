#include "../include/main.h"

static int obtenir_index(std::vector<IndexMap>& table, int& taille_actuelle, const std::string& texte) {
    for (int i = 0; i < taille_actuelle; i++)
        if (table[i].cle == texte) return table[i].index;

    table[taille_actuelle].cle   = texte;
    table[taille_actuelle].index = taille_actuelle;
    return taille_actuelle++;
}

std::unique_ptr<FinancialNDArray> read_file(const std::string& filename, const std::string& sep,
                                            std::vector<IndexMap>& index_actions,
                                            std::vector<IndexMap>& index_dates,
                                            int& nb_actions, int& nb_dates) {
    std::ifstream file(filename);
    if (!file.is_open()) return nullptr;

    // Première passe : collecter tickers et dates
    std::string line;
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        std::string ticker, price_str, date;
        if (std::getline(ss, ticker, sep[0]) &&
            std::getline(ss, price_str, sep[0]) &&
            std::getline(ss, date, sep[0])) {
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
        std::istringstream ss(line);
        std::string ticker, price_str, date;
        if (std::getline(ss, ticker, sep[0]) &&
            std::getline(ss, price_str, sep[0]) &&
            std::getline(ss, date, sep[0])) {
            float price   = std::stof(price_str);
            int ligne     = obtenir_index(index_actions, nb_actions, ticker);
            int colonne   = obtenir_index(index_dates,   nb_dates,   date);
            matrix->data[ligne * matrix->cols + colonne] = price;
        }
    }
    return matrix;
}