#include "../include/header.h"
#include "../include/parser.h"
#include "../include/bourse.h"
#include "../include/book_order.h"

bool verify_buy(const Portfolio& portfolio, float amount, int quantity) {
    if (amount <= 0 || quantity <= 0) return false;
    float cout_total = amount * quantity * (1.0f + FRAIS_COURTAGE_ACHAT);
    return portfolio.cash >= cout_total;
}

bool verify_sell(const Portfolio& portfolio, int quantity, int current_line) {
    if (quantity <= 0) return false;
    return portfolio.shares_owned[current_line] >= quantity;
}

float get_price_safe(const FinancialNDArray& matrix, int action_line, int date_col, int current_sim_col) {
    if (date_col < current_sim_col) return -1.0f;
    return matrix.data[action_line * matrix.cols + date_col];
}

float get_average(const float* arr, int size) {
    if (!arr || size <= 0) return ERROR_VALUE;
    float s = 0;
    for (int i = 0; i < size; i++) s += arr[i];
    return s / size;
}