#include "main.h"

struct Order{
    string symbol;
    double price;
    int quantity;
    bool is_buy;
};

class BacktestEngine{
    private :
        double cash;
        vector<char> actions_owned; /*Exemple : ["AAPL", "GOOG"]*/
        vector<float> actions_qutity; /*[0, 2]*/
    public:
        void process_order(const Order &order) {
        
    }
    double get_balance() const { return cash; }
};