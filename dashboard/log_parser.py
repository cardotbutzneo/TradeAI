"""log_parser.py — Read-only observer of the simulation.

Parses ``src_cpp/bourse.log`` (the file the simulation already writes to) and
reconstructs a structured view of the run: price series per ticker, and per
agent the cash / holdings / trades over time.

This module NEVER imports or touches the simulation code. It only reads the
log file, so it works both live (while a sim is running) and as a replay of a
finished run.

Log lines it understands (they may be interleaved on the same physical line,
because C++ stderr and Python stderr mix, so we match by regex over the whole
text, not line by line):

    [Broker] reçu C++ : 'TICK;2026/07/26-09:30:00;GOOG:144.17:13,APPL:41.08:13,'
    [Python-Debug] [agent_id='agent1'] decision : ['BUY;GOOG;2', 'BUY;APPL;7']
    [agent1] ACK reçu : ACK;agent1;OK;445.913
    [agent2] ACK reçu : ACK;agent2;REJECT_NO_CASH
    [agent1] Fin. Wallet : 16.62€
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

# Starting cash of each agent (see src_python/main.py). Used only to draw the
# performance baseline; edit here if the agents in main.py change.
INITIAL_CASH: dict[str, float] = {"agent1": 1000.0, "agent2": 2000.0, "agent3": 500.0}
DEFAULT_INITIAL = 1000.0

_TICK_RE = re.compile(r"TICK;([^;']+);([^'\n]*)")
_DEC_RE = re.compile(r"\[agent_id='(agent\w+)'\] decision : (\[[^\]]*\])")
_ACK_RE = re.compile(r"\[(agent\w+)\] ACK reçu : ACK;agent\w+;([A-Z_]+)(?:;([-\d.]+))?")
_FIN_RE = re.compile(r"\[(agent\w+)\] Fin\. Wallet : ([-\d.]+)")
_STOP_RE = re.compile(r"reçu C\+\+ : 'STOP'")


@dataclass
class Trade:
    time: str
    ticker: str
    action: str      # BUY | SELL
    qty: int
    status: str      # OK | REJECT


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
    _pending: list[tuple[str, str, int]] = field(default_factory=list)


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


def _agent(state: SimState, aid: str) -> AgentState:
    if aid not in state.agents:
        init = INITIAL_CASH.get(aid, DEFAULT_INITIAL)
        state.agents[aid] = AgentState(agent_id=aid, initial_cash=init, cash=init)
    return state.agents[aid]


def _ensure_ticker(state: SimState, ticker: str, n_ticks: int) -> None:
    if ticker not in state.prices:
        state.tickers.append(ticker)
        # back-fill so every series has the same length as `times`
        state.prices[ticker] = [None] * n_ticks
        state.volumes[ticker] = [0] * n_ticks


def parse_log(path: str) -> SimState:
    """Parse the whole log file into a SimState. Safe to call repeatedly (live)."""
    state = SimState()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except FileNotFoundError:
        return state

    # Collect every event with its position so we can replay them in order.
    events: list[tuple[int, str, re.Match]] = []
    for m in _TICK_RE.finditer(text):
        events.append((m.start(), "tick", m))
    for m in _DEC_RE.finditer(text):
        events.append((m.start(), "dec", m))
    for m in _ACK_RE.finditer(text):
        events.append((m.start(), "ack", m))
    for m in _FIN_RE.finditer(text):
        events.append((m.start(), "fin", m))
    for m in _STOP_RE.finditer(text):
        events.append((m.start(), "stop", m))
    events.sort(key=lambda e: e[0])

    current_time = ""
    last_price: dict[str, float] = {}

    for _, kind, m in events:
        if kind == "tick":
            current_time = _parse_time(m.group(1))
            state.times.append(current_time)
            idx = len(state.times) - 1
            # lengthen every existing series by one slot
            for t in state.tickers:
                state.prices[t].append(None)
                state.volumes[t].append(0)
            # fill in the tickers present in this tick
            for item in m.group(2).split(","):
                if not item.strip():
                    continue
                parts = item.split(":")
                if len(parts) < 3:
                    continue
                ticker, price_s, vol_s = parts[0], parts[1], parts[2]
                _ensure_ticker(state, ticker, len(state.times))
                try:
                    price = float(price_s)
                except ValueError:
                    continue
                state.prices[ticker][idx] = price
                try:
                    state.volumes[ticker][idx] = int(vol_s)
                except ValueError:
                    pass
                last_price[ticker] = price
            # snapshot every agent's net worth at this tick
            for ag in state.agents.values():
                holdings = sum(q * last_price.get(t, 0.0) for t, q in ag.shares.items())
                ag.networth_hist.append(ag.cash + holdings)

        elif kind == "dec":
            ag = _agent(state, m.group(1))
            ag._pending = []
            try:
                orders = ast.literal_eval(m.group(2))
            except (ValueError, SyntaxError):
                orders = []
            for o in orders:
                bits = str(o).split(";")
                if len(bits) < 3:
                    continue
                try:
                    ag._pending.append((bits[0], bits[1], int(bits[2])))
                except ValueError:
                    continue

        elif kind == "ack":
            ag = _agent(state, m.group(1))
            status, cash_s = m.group(2), m.group(3)
            if status == "OK":
                ag.n_ok += 1
                if cash_s:
                    try:
                        ag.cash = float(cash_s)
                    except ValueError:
                        pass
                for action, ticker, qty in ag._pending:
                    if action == "BUY":
                        ag.shares[ticker] += qty
                        ag.n_buy += 1
                    elif action == "SELL":
                        ag.shares[ticker] -= qty
                        ag.n_sell += 1
                    ag.trades.append(Trade(current_time, ticker, action, qty, "OK"))
            elif status.startswith("REJECT"):
                ag.n_reject += 1
                for action, ticker, qty in ag._pending:
                    ag.trades.append(Trade(current_time, ticker, action, qty, "REJECT"))
            ag._pending = []

        elif kind == "fin":
            ag = _agent(state, m.group(1))
            try:
                ag.final_wallet = float(m.group(2))
            except ValueError:
                pass

        elif kind == "stop":
            state.finished = True

    return state


def current_networth(state: SimState, ag: AgentState) -> float:
    """Latest known net worth (cash + holdings at last seen price)."""
    if ag.networth_hist:
        return ag.networth_hist[-1]
    return ag.cash


if __name__ == "__main__":
    import sys

    log = sys.argv[1] if len(sys.argv) > 1 else "../src_cpp/bourse.log"
    s = parse_log(log)
    print(f"ticks={s.n_ticks} tickers={s.tickers} finished={s.finished}")
    for aid, ag in sorted(s.agents.items()):
        print(
            f"  {aid}: cash={ag.cash:.2f} networth={current_networth(s, ag):.2f} "
            f"buys={ag.n_buy} sells={ag.n_sell} rejects={ag.n_reject} "
            f"shares={dict(ag.shares)} final={ag.final_wallet}"
        )
