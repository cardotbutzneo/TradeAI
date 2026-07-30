/**
 * @file log.h
 * @brief Minimal file + stderr logger used across the C++ engine.
 */
#pragma once
#include <fstream>
#include <string>
#include <ctime>
#include <iostream>

/** Severity of a log line; ERROR and WARN are duplicated into the error log. */
enum class LogLevel { INFO, WARN, ERROR, DEBUG };

/**
 * @brief Writes timestamped, leveled log lines to a main log file, mirrors
 *        WARN/ERROR lines into a dedicated error file, and echoes every line
 *        to stderr for terminal visibility.
 *
 * Both files are opened in append mode on construction and closed on
 * destruction (or explicitly via close()/reset()).
 */
class Logger {
private:
    std::string   log_path;
    std::string   err_path;
    std::ofstream log_file;
    std::ofstream err_file;

    /** @brief Maps a LogLevel to its fixed-width string label. */
    std::string level_to_str(LogLevel level) {
        switch (level) {
            case LogLevel::INFO:  return "INFO ";
            case LogLevel::WARN:  return "WARN ";
            case LogLevel::ERROR: return "ERROR";
            case LogLevel::DEBUG: return "DEBUG";
            default:              return "?????";
        }
    }

    /** @brief Formats the current local time as "YYYY/MM/DD-HH:MM:SS". */
    std::string timestamp() {
        std::time_t now = std::time(nullptr);
        std::tm*    ti  = std::localtime(&now);
        char        buf[80];
        std::strftime(buf, sizeof(buf), "%Y/%m/%d-%H:%M:%S", ti);
        return std::string(buf);
    }

    /** @brief Builds a "[timestamp] [level] [source] msg" line. */
    std::string format(LogLevel level, const std::string& source,
                       const std::string& msg) {
        return "[" + timestamp() + "] "
             + "[" + level_to_str(level) + "] "
             + "[" + source + "] "
             + msg;
    }

    /** @brief Formats and dispatches a line to the log file, the error file (if WARN/ERROR) and stderr. */
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
    /**
     * @brief Opens (in append mode) the main and error log files.
     * @param log_path Path of the file receiving every log line.
     * @param err_path Path of the file receiving WARN/ERROR lines only.
     */
    Logger(const std::string& log_path = "logs/simulation.log",
           const std::string& err_path = "logs/error.log")
        : log_path(log_path), err_path(err_path) {
        log_file.open(log_path, std::ios::app);
        err_file.open(err_path, std::ios::app);
        if (!log_file.is_open()) std::cerr << "[Logger] Impossible d'ouvrir " << log_path << "\n";
        if (!err_file.is_open()) std::cerr << "[Logger] Impossible d'ouvrir " << err_path << "\n";
    }

    ~Logger() { close(); }

    /** @brief Logs an informational message. @param source Emitting component name. @param msg Message body. */
    void info (const std::string& source, const std::string& msg) { write(LogLevel::INFO,  source, msg); }
    /** @brief Logs a warning (also mirrored to the error log). @param source Emitting component name. @param msg Message body. */
    void warn (const std::string& source, const std::string& msg) { write(LogLevel::WARN,  source, msg); }
    /** @brief Logs an error (also mirrored to the error log). @param source Emitting component name. @param msg Message body. */
    void error(const std::string& source, const std::string& msg) { write(LogLevel::ERROR, source, msg); }
    /** @brief Logs a debug message. @param source Emitting component name. @param msg Message body. */
    void debug(const std::string& source, const std::string& msg) { write(LogLevel::DEBUG, source, msg); }

    /** @brief Truncates both log files (fresh run) and writes a reset marker. */
    void reset() {
        log_file.close();
        err_file.close();
        log_file.open(log_path, std::ios::trunc);  // trunc = écrase
        err_file.open(err_path, std::ios::trunc);
        info("Logger", "Logs réinitialisés");
    }

    /** @brief Closes both log file handles if open. Safe to call multiple times. */
    void close() {
        if (log_file.is_open()) log_file.close();
        if (err_file.is_open()) err_file.close();
    }
};