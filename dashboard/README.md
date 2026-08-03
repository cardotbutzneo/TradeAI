# TradeAI Dashboard

A live, web-based dashboard to visualize the trading simulation: KPI tiles,
agent leaderboard, net-worth curves, and price charts with each agent's
buy/sell markers — all updating in real time, in a full-width dark layout.

> **It does not touch the simulation logic.** The dashboard is a *read-only
> observer*: every connection it opens to the database the simulation already
> writes to (`data/trading.db`) is read-only. You can run it while a
> simulation is live, or after a run to replay the result.

---

## What you see

| Panel | Content |
|-------|---------|
| **KPI tiles** | Ticks processed, active agents, trades executed, rejected orders, and the current best performer. |
| **Leaderboard** | Agents ranked by net worth, with return %, cash, holdings value, and buy/sell/reject counts. |
| **Net worth over time** | Each agent's equity curve (cash + holdings), with a dotted line at their starting capital. |
| **Prices & trades** | One price chart per ticker (GOOG, APPL…) with ▲ BUY / ▼ SELL markers per agent, placed at the executed price. |

The header shows the TradeAI logo, a **● LIVE / ● FINISHED / ● WAITING** badge, and the tick count.

---

## Run

It's a local script — no server to deploy, no Docker. Two terminals:

**Terminal 1 — start the dashboard:**
```bash
python3 dashboard/app.py
# then open http://127.0.0.1:8050 in your browser
```

**Terminal 2 — run a simulation (the dashboard updates by itself):**
```bash
./run.sh --generate --dur=1 --file=data/small.csv
./run.sh train data/small.csv
```

Watch the charts fill up live while the simulation runs. Dependencies are the
project's usual `pip install -r requirements.txt` (see the repo root).

---

## Options

- **Custom database file** (e.g. to replay another run):
  ```bash
  TRADEAI_DB=/path/to/trading.db python3 app.py
  ```
- **Refresh rate / colors / port**: edit the constants at the top of
  [`app.py`](app.py) (`REFRESH_MS`, `AGENT_COLORS`, the `app.run(... port=8050)` call).

## Files

| File | Role |
|------|------|
| [`db_reader.py`](db_reader.py) | Reads `data/trading.db` (read-only) into a structured `SimState` (prices, agents, trades). Pure, no simulation imports. |
| [`app.py`](app.py) | The Dash web app: builds the figures/KPI tiles and refreshes on a timer. |
| [`assets/style.css`](assets/style.css) | Layout, cards, and the leaderboard table style (auto-loaded by Dash). |
| [`assets/logo.svg`](assets/logo.svg) | The header logo mark. |

## Notes

- Starting capital, strategy and final wallet per agent live in the
  `agents` table (`src_python/dataBase.py`), written once at registration and
  once at shutdown by `run_client.py` — the dashboard no longer hardcodes it.
- Net worth = cash (authoritative, from each `OK` acknowledgement) + holdings
  valued at the last seen price. Holdings are reconstructed from executed
  trades, so treat them as a best-effort estimate.
- Price history comes from the `ticks` table. All three agents observe the
  same broker tick stream and each call `insert_tick`, but a
  `UNIQUE(ticker, date)` constraint (`INSERT OR IGNORE`) keeps that from
  tripling every row.
- Rejected orders are stored in `trades` too (`status` column, e.g.
  `REJECT_NO_CASH`), not just `OK` ones — that's what feeds the "Rejected
  orders" KPI tile.
