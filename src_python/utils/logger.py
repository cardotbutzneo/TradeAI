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

    def _format(self, level: LogLevel, file: str, func: str, msg: str) -> str:
        ts = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        return f"[{ts}] [{level.value}] [{file}] [{func}] {msg}"

    def info(self, file: str, func: str, msg: str):
        line = self._format(LogLevel.INFO, file, func, msg)
        self._log.write(line + "\n")
        print(line, file=sys.stderr)

    def debug(self, file: str, func: str, msg: str):
        line = self._format(LogLevel.DEBUG, file, func, msg)
        self._log.write(line + "\n")

    def warn(self, file: str, func:str, msg: str):
        line = self._format(LogLevel.WARN, file, func, msg)
        self._log.write(line + "\n")
        self._err.write(line + "\n")
        print(line, file=sys.stderr)

    def error(self, file: str, func:str, msg: str):
        line = self._format(LogLevel.ERROR, file, func, msg)
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