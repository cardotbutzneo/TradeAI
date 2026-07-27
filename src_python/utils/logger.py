import sys
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    INFO  = "INFO"
    WARN  = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"

class Logger:
    def __init__(self, log_path="logs/simulation.log",
                       err_path="logs/error.log"):
        import os
        os.makedirs("logs", exist_ok=True)

        self._path_log = log_path
        self._path_err = err_path
        self._log = open(log_path, "a", buffering=1)  # buffering=1 = flush par ligne
        self._err = open(err_path, "a", buffering=1)

    def _format(self, level: LogLevel, source: str, msg: str) -> str:
        ts = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        return f"[{ts}] [{level.value}] [{source}] {msg}"

    def info(self, source: str, msg: str):
        line = self._format(LogLevel.INFO, source, msg)
        self._log.write(line + "\n")
        print(line, file=sys.stderr)

    def debug(self, source: str, msg: str):
        line = self._format(LogLevel.DEBUG, source, msg)
        self._log.write(line + "\n")

    def warn(self, source: str, msg: str):
        line = self._format(LogLevel.WARN, source, msg)
        self._log.write(line + "\n")
        self._err.write(line + "\n")
        print(line, file=sys.stderr)

    def error(self, source: str, msg: str):
        line = self._format(LogLevel.ERROR, source, msg)
        self._err.write(line + "\n")
        print(line, file=sys.stderr)

    def close(self):
        self._log.close()
        self._err.close()

    def reset(self):
        with open(self._path_log, "w") as _:
            pass
        with open(self._path_err, "w") as _:
            pass

logger = Logger()