#pragma once
#include <fstream>
#include <string>
#include <ctime>
#include <iostream>

enum class LogLevel { INFO, WARN, ERROR, DEBUG };

class Logger {
private:
    std::string   log_path;
    std::string   err_path;
    std::ofstream log_file;
    std::ofstream err_file;

    std::string level_to_str(LogLevel level) {
        switch (level) {
            case LogLevel::INFO:  return "INFO ";
            case LogLevel::WARN:  return "WARN ";
            case LogLevel::ERROR: return "ERROR";
            case LogLevel::DEBUG: return "DEBUG";
            default:              return "?????";
        }
    }

    std::string timestamp() {
        std::time_t now = std::time(nullptr);
        std::tm*    ti  = std::localtime(&now);
        char        buf[80];
        std::strftime(buf, sizeof(buf), "%Y/%m/%d-%H:%M:%S", ti);
        return std::string(buf);
    }

    std::string format(LogLevel level, const std::string& source,
                       const std::string& msg) {
        return "[" + timestamp() + "] "
             + "[" + level_to_str(level) + "] "
             + "[" + source + "] "
             + msg;
    }

    void write(LogLevel level, const std::string& source,
               const std::string& msg) {
        std::string line = format(level, source, msg);

        // Toujours dans le log principal
        if (log_file.is_open()) log_file << line << "\n";

        // Erreurs et warnings aussi dans err_file
        if (level == LogLevel::ERROR || level == LogLevel::WARN)
            if (err_file.is_open()) err_file << line << "\n";

        // Affiche dans stderr pour le terminal
        std::cerr << line << "\n";
    }

public:
    Logger(const std::string& log_path = "logs/simulation.log",
           const std::string& err_path = "logs/error.log")
        : log_path(log_path), err_path(err_path) {
        log_file.open(log_path, std::ios::app);
        err_file.open(err_path, std::ios::app);
        if (!log_file.is_open()) std::cerr << "[Logger] Impossible d'ouvrir " << log_path << "\n";
        if (!err_file.is_open()) std::cerr << "[Logger] Impossible d'ouvrir " << err_path << "\n";
    }

    ~Logger() { close(); }

    void info (const std::string& source, const std::string& msg) { write(LogLevel::INFO,  source, msg); }
    void warn (const std::string& source, const std::string& msg) { write(LogLevel::WARN,  source, msg); }
    void error(const std::string& source, const std::string& msg) { write(LogLevel::ERROR, source, msg); }
    void debug(const std::string& source, const std::string& msg) { write(LogLevel::DEBUG, source, msg); }

    void reset() {
        log_file.close();
        err_file.close();
        log_file.open(log_path, std::ios::trunc);  // trunc = écrase
        err_file.open(err_path, std::ios::trunc);
        info("Logger", "Logs réinitialisés");
    }

    void close() {
        if (log_file.is_open()) log_file.close();
        if (err_file.is_open()) err_file.close();
    }
};