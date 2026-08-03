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
                CREATE TABLE IF NOT EXISTS agents (
                    client_id       TEXT PRIMARY KEY,
                    initial_cash    REAL NOT NULL,
                    strategy        TEXT,
                    finished_wallet REAL,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
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
                    date     TEXT NOT NULL,
                    UNIQUE(ticker, date)
                );
            """)
            # Migration for databases created before `status`/`date` existed on
            # `trades` (simulated time differs from `created_at`'s wall clock,
            # and rejected orders need a place to live other than the log).
            existing_cols = {row[1] for row in self.conn.execute("PRAGMA table_info(trades)")}
            if "status" not in existing_cols:
                self.conn.execute("ALTER TABLE trades ADD COLUMN status TEXT NOT NULL DEFAULT 'OK'")
            if "date" not in existing_cols:
                self.conn.execute("ALTER TABLE trades ADD COLUMN date TEXT")
            # Migration: an older `ticks` table has no UNIQUE(ticker, date), which
            # every agent's run_client now relies on to de-duplicate — all agents
            # observe the same broker tick stream and would otherwise triple-insert.
            (ticks_sql,) = self.conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='ticks'"
            ).fetchone() or (None,)
            if ticks_sql and "UNIQUE" not in ticks_sql.upper():
                self.conn.executescript("""
                    ALTER TABLE ticks RENAME TO ticks_old;
                    CREATE TABLE ticks (
                        id       INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker   TEXT NOT NULL,
                        price    REAL NOT NULL,
                        volume   INTEGER,
                        date     TEXT NOT NULL,
                        UNIQUE(ticker, date)
                    );
                    INSERT OR IGNORE INTO ticks (ticker, price, volume, date)
                        SELECT ticker, price, volume, date FROM ticks_old;
                    DROP TABLE ticks_old;
                """)
            self.conn.commit()

    def register_agent(self, client_id, initial_cash, strategy=""):
        """Record an agent's starting cash once, at registration time.

        Idempotent (INSERT OR IGNORE): safe to call again if a client
        reconnects mid-run without resetting its recorded initial cash.
        """
        with self.lock:
            self.conn.execute("""
                INSERT OR IGNORE INTO agents (client_id, initial_cash, strategy)
                VALUES (?, ?, ?)
            """, (client_id, initial_cash, strategy))
            self.conn.commit()

    def insert_trade(self, client_id, ticker, action,
                     price, quantity, cash_after, status="OK", date=None, tx_id=""):
        with self.lock:
            self.conn.execute("""
                INSERT INTO trades
                (client_id, ticker, action, price, quantity, cash_after, status, date, transaction_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, ticker, action, price, quantity, cash_after, status, date, tx_id))
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
        # OR IGNORE: every agent's run_client observes the same broker tick
        # stream and calls this independently, so (ticker, date) collisions
        # are expected duplicates, not errors.
        with self.lock:
            self.conn.execute(
                "INSERT OR IGNORE INTO ticks (ticker, price, volume, date) VALUES (?,?,?,?)",
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

    def mark_finished(self, client_id, wallet):
        with self.lock:
            self.conn.execute(
                "UPDATE agents SET finished_wallet = ? WHERE client_id = ?",
                (wallet, client_id)
            )
            self.conn.commit()

    def get_agents(self) -> list:
        with self.lock:
            cursor = self.conn.execute(
                "SELECT client_id, initial_cash, strategy, finished_wallet FROM agents ORDER BY client_id"
            )
            return cursor.fetchall()

    def get_ticks(self) -> list:
        """All ticks in insertion order — the simulation's price feed history."""
        with self.lock:
            cursor = self.conn.execute(
                "SELECT ticker, price, volume, date FROM ticks ORDER BY id"
            )
            return cursor.fetchall()

    def get_trades(self, client_id=None) -> list:
        # ORDER BY id, not created_at: several trades can land in the same
        # wall-clock second, but id always reflects true insertion order.
        with self.lock:
            if client_id:
                cursor = self.conn.execute(
                    "SELECT * FROM trades WHERE client_id = ? ORDER BY id",
                    (client_id,)
                )
            else:
                cursor = self.conn.execute("SELECT * FROM trades ORDER BY id")
            return cursor.fetchall()

    def reset(self):
        with self.lock:
            self.conn.executescript("""
                DELETE FROM agents;
                DELETE FROM portfolio;
                DELETE FROM trades;
                DELETE FROM ticks;
            """)
            self.conn.commit()

    def close(self):
        self.conn.close()