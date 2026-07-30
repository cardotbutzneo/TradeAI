#include "../include/header.h"
#include "../include/bourse.h"
#include "../include/book_order.h"

static int get_or_create_index(std::vector<IndexMap>& table, int& current_size, const std::string& text) {
    for (int i = 0; i < current_size; i++)
        if (table[i].key == text) return table[i].index;

    if (current_size >= (int)table.size()){
        // grow the vector when full
        table.resize(table.size() + 200); // grow by 200 at a time to avoid excessive memory use
    }
    table[current_size].key   = text;
    table[current_size].index = current_size;
    return current_size++;
}

std::string trim(const std::string& str) {
    const std::string whitespace = " \t\n\r\f\v";
    size_t start = str.find_first_not_of(whitespace);
    if (start == std::string::npos) return ""; // Empty or all whitespace

    size_t end = str.find_last_not_of(whitespace);
    return str.substr(start, end - start + 1);
}

std::unique_ptr<FinancialNDArray> read_file(std::istream& file, const std::string& sep,
                                            std::vector<IndexMap>& stock_index,
                                            std::vector<IndexMap>& date_index,
                                            map<std::string, Action>& stocks,
                                            vector<long long>& volumes,
                                            int& nb_stocks, int& nb_dates) {

    // First pass: collect tickers and dates
    std::string line, ticker, price_str, date, volume_str, currency, hash;
    line.reserve(256); // reserve 256 bytes for the line

    while (getline(file, line)) { // file or stdin
        istringstream ss(line);
        if (getline(ss, date, sep[0]) &&
            getline(ss, ticker, sep[0]) &&
            getline(ss, price_str, sep[0]) &&
            getline(ss, volume_str, sep[0]) &&
            getline(ss, currency, sep[0]) &&
            getline(ss, hash, sep[0])
        ) {
            get_or_create_index(stock_index, nb_stocks, ticker);
            get_or_create_index(date_index,  nb_dates,  date);
        }
    }

    auto matrix       = std::make_unique<FinancialNDArray>();
    matrix->rows      = nb_stocks;
    matrix->cols      = nb_dates;
    matrix->data.assign(nb_stocks * nb_dates, -1.0f);

    // Second pass: fill the matrix
    file.clear();
    file.seekg(0);
    while (std::getline(file, line)) {
        istringstream ss(line);
        string ticker, price_str, date, volume_str;
        if (getline(ss, date, sep[0]) &&
            getline(ss, ticker, sep[0]) &&
            getline(ss, price_str, sep[0]) &&
            getline(ss, volume_str, sep[0]) &&
            getline(ss, currency, sep[0]) &&
            getline(ss, hash, sep[0])) {
            float price   = std::stof(price_str);
            long long volume = volume_str.empty() ? 0LL : stoll(volume_str);
            int row       = get_or_create_index(stock_index, nb_stocks, ticker);
            int col       = get_or_create_index(date_index,  nb_dates,  date);
            matrix->data[row * matrix->cols + col] = price;
            volumes.push_back(volume);

            auto& stock = stocks[ticker];
            stock.id = ticker;
            stock.last_traded_price = price;
            stock.current_volume += volume;

            if (stock.total_shares == 0){
                stock.total_shares = volume;
            }
        }
    }
    return matrix;
}
