# database.py
import sqlite3
import threading
from datetime import datetime

class Database:
    def __init__(self, path: str = "data/trading.db"):
        self.path = path
        # check_same_thread=False car asyncio utilise plusieurs threads
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()  # évite les accès concurrents
        self._create_tables()

    def _create_tables(self):
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id   TEXT NOT NULL,
                    ticker      TEXT NOT NULL,
                    quantity    INTEGER DEFAULT 0,
                    avg_price   REAL DEFAULT 0.0,
                    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(client_id, ticker)
                );
                CREATE TABLE IF NOT EXISTS trades (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id      TEXT NOT NULL,
                    ticker         TEXT NOT NULL,
                    action         TEXT NOT NULL,
                    price          REAL NOT NULL,
                    quantity       INTEGER NOT NULL,
                    cash_after     REAL NOT NULL,
                    transaction_id TEXT,
                    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS ticks (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker   TEXT NOT NULL,
                    price    REAL NOT NULL,
                    volume   INTEGER,
                    date     TEXT NOT NULL
                );
            """)
            self.conn.commit()

    def insert_trade(self, client_id, ticker, action,
                     price, quantity, cash_after, tx_id=""):
        with self.lock:
            self.conn.execute("""
                INSERT INTO trades
                (client_id, ticker, action, price, quantity, cash_after, transaction_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (client_id, ticker, action, price, quantity, cash_after, tx_id))
            self.conn.commit()

    def update_portfolio(self, client_id, ticker, quantity, avg_price):
        with self.lock:
            self.conn.execute("""
                INSERT INTO portfolio (client_id, ticker, quantity, avg_price, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(client_id, ticker) DO UPDATE SET
                    quantity  = excluded.quantity,
                    avg_price = excluded.avg_price,
                    updated_at = CURRENT_TIMESTAMP
            """, (client_id, ticker, quantity, avg_price))
            self.conn.commit()

    def insert_tick(self, ticker, price, volume, date):
        with self.lock:
            self.conn.execute(
                "INSERT INTO ticks (ticker, price, volume, date) VALUES (?,?,?,?)",
                (ticker, price, volume, date)
            )
            self.conn.commit()

    def get_portfolio(self, client_id) -> list:
        with self.lock:
            cursor = self.conn.execute(
                "SELECT ticker, quantity, avg_price FROM portfolio WHERE client_id = ?",
                (client_id,)
            )
            return cursor.fetchall()

    def get_trades(self, client_id=None) -> list:
        with self.lock:
            if client_id:
                cursor = self.conn.execute(
                    "SELECT * FROM trades WHERE client_id = ? ORDER BY created_at",
                    (client_id,)
                )
            else:
                cursor = self.conn.execute("SELECT * FROM trades ORDER BY created_at")
            return cursor.fetchall()

    def reset(self):
        with self.lock:
            self.conn.executescript("""
                DELETE FROM portfolio;
                DELETE FROM trades;
                DELETE FROM ticks;
            """)
            self.conn.commit()

    def close(self):
        self.conn.close()