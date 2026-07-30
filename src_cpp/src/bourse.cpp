#include "../include/header.h"
#include "../include/parser.h"
#include "../include/bourse.h"
#include "../include/book_order.h"

bool verify_buy(const AccountType& account, float amount, int quantity) {
    if (amount <= 0 || quantity <= 0) return false;
    float total_cost = amount * quantity * (1.0f + BUY_FEE_RATE);
    return account.cash >= total_cost;
}

bool verify_sell(const AccountType& account, int quantity, int stock_idx) {
    if (quantity <= 0) return false;
    return account.shares_owned[stock_idx] >= quantity;
}

float get_price_safe(const FinancialNDArray& matrix, int stock_line, int date_col, int current_sim_col) {
    if (date_col < current_sim_col) return -1.0f;
    return matrix.data[stock_line * matrix.cols + date_col];
}

float get_average(const float* arr, int size) {
    if (!arr || size <= 0) return ERROR_VALUE;
    float s = 0;
    for (int i = 0; i < size; i++) s += arr[i];
    return s / size;
}
