"""db_reader.py — Read-only observer of the simulation, via its SQLite database.

Reads ``data/trading.db`` (the DB the simulation already writes to through
``src_python/dataBase.py``) and reconstructs the same structured view of the
run that the dashboard needs: price series per ticker, and per agent the
cash / holdings / trades over time.

This module NEVER imports or touches the simulation code, and never writes to
the database — every connection is opened read-only. It works both live
(while a sim is running) and as a replay of a finished run.

Tables it reads (see ``src_python/dataBase.py`` for the schema):

    agents    — one row per registered agent: starting cash, strategy,
                and (once the run ends) its final wallet.
    ticks     — the price feed: one row per (ticker, simulated timestamp).
    trades    — one row per executed order attempt, OK or rejected, carrying
                the simulated timestamp of the tick that triggered it.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from itertools import groupby
from pathlib import Path

DEFAULT_INITIAL = 1000.0


@dataclass
class Trade:
    time: str
    ticker: str
    action: str      # BUY | SELL
    qty: int
    status: str      # OK | REJECT_*


@dataclass
class AgentState:
    agent_id: str
    initial_cash: float
    cash: float
    shares: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    trades: list[Trade] = field(default_factory=list)
    networth_hist: list[float] = field(default_factory=list)   # sampled per tick
    n_buy: int = 0
    n_sell: int = 0
    n_ok: int = 0
    n_reject: int = 0
    final_wallet: float | None = None


@dataclass
class SimState:
    tickers: list[str] = field(default_factory=list)
    times: list[str] = field(default_factory=list)              # tick timestamps
    prices: dict[str, list[float]] = field(default_factory=dict)  # ticker -> per-tick price
    volumes: dict[str, list[int]] = field(default_factory=dict)
    agents: dict[str, AgentState] = field(default_factory=dict)
    finished: bool = False

    @property
    def n_ticks(self) -> int:
        return len(self.times)


def _parse_time(raw: str) -> str:
    """'2026/07/26-09:30:00' -> ISO-ish string Plotly can read on a time axis."""
    try:
        return datetime.strptime(raw, "%Y/%m/%d-%H:%M:%S").isoformat()
    except ValueError:
        return raw


def _agent(state: SimState, aid: str, initial_cash: float = DEFAULT_INITIAL) -> AgentState:
    if aid not in state.agents:
        state.agents[aid] = AgentState(agent_id=aid, initial_cash=initial_cash, cash=initial_cash)
    return state.agents[aid]


def _ensure_ticker(state: SimState, ticker: str, n_ticks: int) -> None:
    if ticker not in state.prices:
        state.tickers.append(ticker)
        # back-fill so every series has the same length as `times`
        state.prices[ticker] = [None] * n_ticks
        state.volumes[ticker] = [0] * n_ticks


def _connect_readonly(path: str) -> sqlite3.Connection | None:
    """Open the DB read-only so the dashboard can never corrupt or lock it.

    Returns None if the file doesn't exist yet (no simulation has run).

    SQLite's URI filenames want forward slashes and (on Windows) a
    `file:///C:/...` triple-slash form — `Path.as_uri()` handles that
    platform difference, a plain f-string would not.
    """
    try:
        uri = Path(path).resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("SELECT 1")  # fails fast if the file/schema isn't there yet
        return conn
    except sqlite3.OperationalError:
        return None


def parse_db(path: str) -> SimState:
    """Read the whole database into a SimState. Safe to call repeatedly (live)."""
    state = SimState()
    conn = _connect_readonly(path)
    if conn is None:
        return state

    try:
        agent_rows = conn.execute(
            "SELECT client_id, initial_cash, finished_wallet FROM agents ORDER BY client_id"
        ).fetchall()
        tick_rows = conn.execute(
            "SELECT ticker, price, volume, date FROM ticks ORDER BY id"
        ).fetchall()
        trade_rows = conn.execute(
            "SELECT client_id, ticker, action, price, quantity, cash_after, status, date "
            "FROM trades ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    for client_id, initial_cash, _ in agent_rows:
        _agent(state, client_id, initial_cash)

    # --- price series, replaying ticks grouped by simulated timestamp so a
    # ticker missing from one tick still lengthens every other series (as the
    # simulation's own TICK messages do — one row per ticker per timestamp). ---
    time_index: dict[str, int] = {}
    for date, rows in groupby(tick_rows, key=lambda r: r[3]):
        idx = len(state.times)
        state.times.append(_parse_time(date))
        for t in state.tickers:
            state.prices[t].append(None)
            state.volumes[t].append(0)
        for ticker, price, volume, _ in rows:
            _ensure_ticker(state, ticker, len(state.times))
            state.prices[ticker][idx] = price
            state.volumes[ticker][idx] = volume
        time_index[date] = idx

    trades_by_date: dict[str, list[tuple]] = defaultdict(list)
    for client_id, ticker, action, price, quantity, cash_after, status, date in trade_rows:
        trades_by_date[date].append((client_id, ticker, action, quantity, cash_after, status))

    # --- replay trades in simulated-time order, snapshotting each agent's net
    # worth at every tick (cash, authoritative from the last OK ack, plus
    # holdings valued at the last seen price) — same model the log parser used. ---
    last_price: dict[str, float] = {}
    for date, idx in time_index.items():
        for t in state.tickers:
            p = state.prices[t][idx]
            if p is not None:
                last_price[t] = p

        for client_id, ticker, action, quantity, cash_after, status in trades_by_date.get(date, []):
            ag = _agent(state, client_id)
            if status == "OK":
                ag.n_ok += 1
                ag.cash = cash_after
                if action == "BUY":
                    ag.shares[ticker] += quantity
                    ag.n_buy += 1
                elif action == "SELL":
                    ag.shares[ticker] -= quantity
                    ag.n_sell += 1
            else:
                ag.n_reject += 1
            ag.trades.append(Trade(_parse_time(date), ticker, action, quantity, status))

        for ag in state.agents.values():
            holdings = sum(q * last_price.get(t, 0.0) for t, q in ag.shares.items())
            ag.networth_hist.append(ag.cash + holdings)

    for client_id, _, finished_wallet in agent_rows:
        if finished_wallet is not None:
            _agent(state, client_id).final_wallet = finished_wallet

    state.finished = bool(agent_rows) and all(fw is not None for _, _, fw in agent_rows)

    return state


def current_networth(state: SimState, ag: AgentState) -> float:
    """Latest known net worth (cash + holdings at last seen price)."""
    if ag.networth_hist:
        return ag.networth_hist[-1]
    return ag.cash


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "../data/trading.db"
    s = parse_db(db_path)
    print(f"ticks={s.n_ticks} tickers={s.tickers} finished={s.finished}")
    for aid, ag in sorted(s.agents.items()):
        print(
            f"  {aid}: cash={ag.cash:.2f} networth={current_networth(s, ag):.2f} "
            f"buys={ag.n_buy} sells={ag.n_sell} rejects={ag.n_reject} "
            f"shares={dict(ag.shares)} final={ag.final_wallet}"
        )
