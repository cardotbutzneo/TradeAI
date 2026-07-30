/**
 * @file bourse.cpp
 * @brief Account/price validation helpers used before an order is accepted
 *        into an OrderBook (see include/bourse.h for the declarations).
 */
#include "../include/header.h"
#include "../include/parser.h"
#include "../include/bourse.h"
#include "../include/book_order.h"

/** @brief True if `account` has enough cash to buy `quantity` shares at `amount` including BUY_FEE_RATE; false for non-positive amount/quantity. */
bool verify_buy(const AccountType& account, float amount, int quantity) {
    if (amount <= 0 || quantity <= 0) return false;
    float total_cost = amount * quantity * (1.0f + BUY_FEE_RATE);
    return account.cash >= total_cost;
}

/** @brief True if `account` owns at least `quantity` shares at index `stock_idx`; false for non-positive quantity. */
bool verify_sell(const AccountType& account, int quantity, int stock_idx) {
    if (quantity <= 0) return false;
    return account.shares_owned[stock_idx] >= quantity;
}

/** @brief Returns matrix.data[stock_line][date_col], or -1 if `date_col` is before `current_sim_col`. */
float get_price_safe(const FinancialNDArray& matrix, int stock_line, int date_col, int current_sim_col) {
    if (date_col < current_sim_col) return -1.0f;
    return matrix.data[stock_line * matrix.cols + date_col];
}

/** @brief Arithmetic mean of `arr[0..size)`; returns ERROR_VALUE if `arr` is null or `size <= 0`. */
float get_average(const float* arr, int size) {
    if (!arr || size <= 0) return ERROR_VALUE;
    float s = 0;
    for (int i = 0; i < size; i++) s += arr[i];
    return s / size;
}
