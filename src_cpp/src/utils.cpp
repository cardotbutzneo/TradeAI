#include "../include/header.h"
#include "../include/bourse.h"
#include "../include/log.h"

#include <thread>
#include <mutex>
#include <queue>
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>

std::queue<std::string> ordre_queue;
std::mutex queue_mutex;

std::map<std::string, std::string> parse_arguments(int argc, char *argv[]) {
    Logger logger;
    std::map<std::string, std::string> args;

    if (argc < 2) {
        logger.error("C++_Main", "Erreur pas de mode trouvé.\n Arret du programme...");
        exit(static_cast<int>(ExitCode::INVALIDE_ARG));
    }

    std::string mode = argv[1];
    if (mode != "prod" && mode != "train") {
        logger.error("Main", "Erreur de parametre : veuillez mettre train ou prod");
        exit(static_cast<int>(ExitCode::INVALIDE_ARG));
    }

    args["mode"] = mode;
    args["fast"] = "false";
    args["input"] = "";

    for (int i = 2; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--fast") {
            args["fast"] = "true";
        } else if (args["input"].empty()) {
            args["input"] = arg;
        }
    }

    logger.debug("Main", "Mode: " + args["mode"] + " fast: " + args["fast"]);
    return args;
}

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

void add_new_client(std::map<std::string, Client>& list_client,
                    const std::string& client_id,
                    const std::string& client_name,
                    int nb_actions,
                    float cash_initial = 1000.0f) {

    Client new_client;
    new_client.id   = client_id;
    new_client.name = client_name;

    // Crée les deux comptes par défaut
    for (const std::string& account_type : {"CTO", "PEA"}) {
        AccountType account;
        account.name = account_type;
        account.cash = cash_initial;
        account.shares_owned.assign(nb_actions, 0);
        new_client.portfolios[account_type] = account;
    }

    list_client[client_id] = new_client;
}

std::string generate_transaction_id(const std::string& buyer,
                                    const std::string& seller,
                                    const std::string& ticker,
                                    double price, long long qty) {
    std::ostringstream raw;
    raw << buyer << seller << ticker
        << std::fixed << std::setprecision(2) << price
        << qty << std::time(nullptr);

    std::string input = raw.str();
    unsigned char digest[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const unsigned char*>(input.c_str()),
           input.size(), digest);

    std::ostringstream hex;
    for (int i = 0; i < 16; i++)
        hex << std::hex << std::setw(2) << std::setfill('0') << (int)digest[i];
    return hex.str();
}

void record_trade(Client& client,
                  const std::string& account_type,  // "CTO" ou "PEA"
                  const std::string& ticker,
                  const std::string& action,
                  double price, long long qty,
                  int idx_action) {

    if (client.portfolios.find(account_type) == client.portfolios.end()) {
        return;  // compte inexistant
    }

    AccountType& account = client.portfolios[account_type];

    Trade t;
    t.ticker         = ticker;
    t.price          = price;
    t.quantity       = qty;
    t.timestamp      = std::time(nullptr);
    t.transaction_id = generate_transaction_id(
        client.id, "MARKET", ticker, price, qty
    );

    if (action == "BUY") {
        t.buyer  = client.id;
        t.seller = "MARKET";
        account.cash -= price * qty * (1 + FRAIS_COURTAGE_ACHAT);
        account.shares_owned[idx_action] += qty;
    } else {
        t.buyer  = "MARKET";
        t.seller = client.id;
        account.cash += price * qty * (1 - FRAIS_COURTAGE_VENTE);
        account.shares_owned[idx_action] -= qty;
    }

    account.trade_history.push_back(t);
}

// load ressources for the matrix

auto get_price_matrix(vector<IndexMap>& index_actions, 
                    vector<IndexMap>& index_dates,
                    int& nb_actions, 
                    int& nb_dates,
                    std::map<std::string, Action>& liste_des_actions,
                    vector<long long>& liste_des_quantites,
                    Logger logger,
                    int argc, char *argv[]) {

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

    std::unique_ptr<FinancialNDArray> matrix = read_file(*source, ",", index_actions, index_dates,
                            liste_des_actions, liste_des_quantites, nb_actions, nb_dates);
    if (!matrix) {
        logger.error("Main", "Fichier csv non trouvé ou inexistant");
        cout << "STOP" << endl;
        return static_cast<int>(ExitCode::ENGINE_CRASH);
    }
}