#pragma once

#include "header.h"
#include <cmath>

#define CONST_MALUS 0.01 // 1% tous les 10% au dessus du volume échangé

/**Création d'une entité de banque autonome gérant les carnets d'odre
 * fichier utiliser en mode prod
*/

/**To Do : Objectif : gerer le volume et le prix des actions avec un nouveau fichier.
 * Possibilité de simuler sur ce systeme ou sur les données historiques
 * 1. Gérer les carnets d'ordre en calculant le volume des actions de facon réalise (en fonction d'un % du capital de l'entreprise)
 * 2. Le cpp ne doit pas attendre le python avant de continuer, le cpp envoie des données en continue (des fractions toutes les 30s dans la realité disons). main.cpp doit servir de brokeur, et python comme client.
 * 3. Pouvoir brancher plusieurs scripts python au cpp pour simuler plusieurs achteur avec differente strategie
 * 4. Ameliorer le systeme de gestion avec l'ajout d'un carnet d'odre poussé (gestion de gros volume, frais de courtage non fixe, etc... -- peut etre ajouté a la phase 1 si prend pas trop de temps)
 * 
 * Refactor to do : 
 * 1. Création du carnet d'odre avec de vrai achat et vente d'actions. On ne suppose pas qu'il y a une quantité infini d'actions
 * 2. Ajout des regles des marchés pour le carnet d'odre
 * 3. 2-3
 */ 

/**Sens de fonctionnement : 
 * serveur (cpp) : tourne tout seul en générant les prix en fonction du volume échangé, ou utilise les prix historique via stdin
 * client (python) : récupère les valeurs a chaque instant via stdout du cpp et envoie des ordre (achat, vente ou rien) via stdin du cpp
 * => les deux boucles l'un sur l'autre mais indépendament
 * 2 modes pour cpp : 
 * --train : récupère les données historique via le stdout d'un autre programme (ou de la matrice pour l'instant)
 * --prod  : joue le role d'une banque / brokeur. Génère les prix de facon dynamique (nécessite plusieurs clients assez dur a mettre en place) 
 */

enum class OrderType { BUY, SELL };

struct Order {
    std::string buying_client;
    std::string selling_client;
    OrderType side;        // BUY ou SELL
    double price;          // Le prix limite demandé
    long long quantity;    // Le nombre d'actions demandées
};

struct Trade {
    std::string transaction_id;
    std::string ticker;
    std::string buyer;
    std::string seller;
    double      price;
    long long   quantity;
    time_t      timestamp;
};

class OrderBook {
private:
    // Trié par prix décroissant (le plus haut prix d'achat en premier)
    std::multimap<double, Order, std::greater<double>> bids;
    
    // Trié par prix croissant (le prix de vente le moins cher en premier)
    std::multimap<double, Order, std::less<double>> asks;

public:
    long long total_quantity; // le nombre d'action totale
    double best_bid = 0.0;
    double best_ask = 0.0;
    std::vector<Trade> trade_history; // historique des trades passés

    // Fonction maîtresse : ajoute un ordre et essaie de le faire correspondre (Matching Engine)
    void process_order(const Order& new_order) {
        if (new_order.side == OrderType::BUY) {
            match_buy_order(new_order);
        } else {
            match_sell_order(new_order);
        }
        update_market_prices();
    }

private:
    long long execute_trade(Order &buyer, Order &seller, double trade_price){
        long long traded_qty = std::min(buyer.quantity, seller.quantity);

        buyer.quantity -= traded_qty;
        seller.quantity -= traded_qty;

        Trade t;
        t.transaction_id = generate_transaction_id(buyer, seller, trade_price);
        t.buyer = buyer.buying_client;
        t.seller = seller.selling_client;
        t.price = trade_price;
        t.quantity = traded_qty;
        t.timestamp = std::time(nullptr);
        trade_history.push_back(t);

        std::cerr << "[TRADE] " << t.buyer << " achète " << traded_qty
                  << " actions de " << t.seller << " à " << trade_price << "\n";

        return traded_qty;
    }

    std::string generate_transaction_id(const Order& buyer, const Order& seller, double price){
        std::ostringstream raw;
        raw << buyer.buying_client << seller.selling_client << std::fixed << std::setprecision(2) << price << std::time(nullptr); // hash
        return raw.str().substr(0, 32);
    }

    void match_buy_order(Order buy_order) {
        // Tant qu'il y a des vendeurs et que le prix d'achat couvre le prix de vente le moins cher
        while (!OrderBook::asks.empty() && buy_order.price >= asks.begin()->first && buy_order.quantity > 0) {
            auto best_ask_it = asks.begin();
            Order& sell_order = best_ask_it->second;

            // Calcul de la quantité échangée (le minimum des deux)
            long long traded_qty = std::min(buy_order.quantity, sell_order.quantity);
            
            // ICI : Le trade d'un volume 'traded_qty' a lieu au prix 'sell_order.price' !


            buy_order.quantity -= traded_qty;
            sell_order.quantity -= traded_qty;

            if (sell_order.quantity == 0) {
                OrderBook::asks.erase(best_ask_it); // L'ordre de vente est totalement exécuté
            }
        }
        // S'il reste de la quantité non achetée, on coupe l'ordre en deux et le replace dans le carnet
        if (buy_order.quantity > 0) {
           OrderBook::bids.insert({buy_order.price, buy_order});
        }
    }

    void match_sell_order(Order sell_order) {
    while (!bids.empty() && sell_order.price <= bids.begin()->first && sell_order.quantity > 0) {
        auto best_bid_it = bids.begin();
        Order& buy_order = best_bid_it->second;

        long long traded_qty = std::min(sell_order.quantity, buy_order.quantity);

        sell_order.quantity -= traded_qty;
        buy_order.quantity  -= traded_qty;

        if (buy_order.quantity == 0) {
            bids.erase(best_bid_it);
        }
    }

    if (sell_order.quantity > 0) {
        asks.insert({sell_order.price, sell_order});
    }
}

    void update_market_prices() {
        if (!OrderBook::bids.empty()) best_bid = OrderBook::bids.begin()->first;
        if (!OrderBook::asks.empty()) best_ask = OrderBook::asks.begin()->first;
    }

    public:
        // Affiche l'état du carnet comme dans ton exemple
        void print_orderbook(const std::string& ticker) const {
            std::cout << "\n=== CARNET " << ticker << " ===\n";
            std::cout << "ASKS (vendeurs) :\n";
            for (auto& [price, order] : asks)
                std::cout << "  SELL;" << ticker << ";" << order.quantity
                        << ";" << price << ";" << order.selling_client << "\n";

            std::cout << "BIDS (acheteurs) :\n";
            for (auto& [price, order] : bids)
                std::cout << "  BUY;" << ticker << ";" << order.quantity
                        << ";" << price << ";" << order.buying_client << "\n";
        }

        void print_trade_history(const std::string& ticker) const {
            std::cout << "\n=== HISTORIQUE TRADES " << ticker << " ===\n";
            for (auto& t : trade_history)
                std::cout << "  " << t.buyer << " <- " << t.quantity
                        << " actions <- " << t.seller
                        << " à " << t.price << "\n";
        }
};

class Action {
public:
    std::string id;               // nom de l'action
    long long total_shares;       // Nombre total d'actions existantes de l'entreprise
    double last_traded_price;     // Le dernier prix auquel une transaction a VRAIMENT eu lieu
    long long current_volume;     // Volume cumulé échangé dans la journée
    
    OrderBook order_book;         // Le carnet d'ordres de cette action

    float return_progressive_malus(long long x) {
        if (current_volume == 0.0f) return 0.0f;
        long long threshold = 0.1 * current_volume; // 10% du total échangé pour l'instant
        if (threshold <= 0) return 0.0f;
        double excess           = static_cast<double>(x - threshold);
        double penalty_fraction = excess / threshold; // ratio au-dessus du seuil
        return static_cast<float>(CONST_MALUS * penalty_fraction);
    }
};