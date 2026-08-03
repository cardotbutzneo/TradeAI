# TradeAI

## Overview
TradeAI is an educational project designed to explore fundamental concepts of **quantitative finance**, **inter-process communication (IPC)**, and **applied mathematics**.

The goal of this project is to build a high-performance market simulator in C++ linked with several algorithmic trading agents in Python. The architecture is designed to evolve progressively as new systems and software engineering concepts are implemented.

## Architecture
The simulation is split across several cooperating components:

1. **Market Simulation Engine (C++, `src_cpp/`)** — a single subprocess, driven over stdin/stdout.
   - Replays a price matrix tick by tick and broadcasts `TICK;...` lines.
   - Order-book matching (`OrderBook`, price-time priority) and a volumetric-impact penalty (`Action::compute_penalty`) on oversized orders.
   - Tracks per-client cash/portfolios and replies with one `ACK;...` line per order.

2. **Broker (Python, `src_python/broker.py`)** — spawns the C++ engine and bridges it to the agents over two local WebSocket servers: one broadcasting ticks (`:8765`), one relaying orders/ACKs (`:8766`).

3. **Trading Agents (Python, `src_python/run_client.py`, `AI.py`)** — one process per agent, each with its own wallet and strategy (`mean_reversion`, `momentum`, `rsi_contrarian`, or a trained neural net via `train_AI.py`). Agents connect to the broker, receive ticks, and send `BUY`/`SELL`/`PASS` decisions.

4. **Persistence (`src_python/dataBase.py`, SQLite at `data/trading.db`)** — every tick, trade (including rejections) and agent outcome is recorded, written only by the simulation.

5. **Dashboard (`dashboard/`)** — a live, read-only Dash web app that visualizes a run (or replays a finished one) straight from `data/trading.db`. See [`dashboard/README.md`](dashboard/README.md).

6. **Synthetic data generator (`src_python/data_generator.py`)** — produces historical CSV price feeds via a Geometric Brownian Motion, used as input for `train` mode.

## Requirements
To compile and run this project, you need:

- A **C++17 compiler** (`g++`, see `src_cpp/makefile`)
- **Python 3.9+**
- The packages listed in `requirements.txt`:
  - `numpy`, `matplotlib` — data generation and offline plotting
  - `websockets` — broker <-> agents transport
  - `dash`, `plotly` — the live dashboard

## Setup
It is highly recommended to use an isolated Python **virtual environment**.

### 1. Initialize the Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Run the simulation
The project includes an orchestrator Bash script `run.sh` to manage compilation, data generation, and execution.

### General usage
```bash
./run.sh <command> [options]
```

### Available commands
- `./run.sh --generate [--file=PATH] [--fdate=YYYY-MM-DD] [--dur=DAYS]` — triggers the Python data generator to build historical synthetic market ticks (GOOG + APPL). See [`help/generate.md`](help/generate.md).
- `./run.sh train FILE [--fast] [--clients N]` — compiles the C++ engine and runs the simulation over a historical CSV file (`--clients` agents in parallel, default 3). See [`help/run.md`](help/run.md).
- `./run.sh prod [--fast] [--clients N]` — same as `train`, but streams data over stdin instead of a file. **Work in progress** — use `train` for now.
- `./run.sh --clean [all]` — removes local logs, `.last_run`, `data/`, and the compiled C++ binary; `all` also removes `config/`. See [`help/clean.md`](help/clean.md).
- `./run.sh help` — prints the Python CLI's own usage (`train`/`prod` arguments). The `help/*.md` files above are a hand-written extended manual, not printed by this command.

### Watching a run live
In a second terminal, while (or after) a simulation runs:
```bash
python3 dashboard/app.py
# then open http://127.0.0.1:8050
```

## Known Limitations
- **`prod` mode** (live stdin feed) is implemented on both sides but not yet exercised end-to-end — stick to `train` mode.
- **Order-book pricing**: the C++ `OrderBook` matches orders by price-time priority, but executed trades are still recorded at the tick price rather than the matched counterparty price — full order-book-driven pricing is not wired in yet.
- **Neural-net strategy** (`AI.strat`, backed by `train_AI.NeuralNetwork`) exists but isn't trained/selected by the default run (`src_python/main.py` only spawns `mean_reversion`, `momentum` and `rsi_contrarian` agents).

## Roadmap
- [x] Asynchronous networking: multi-client WebSocket broker relaying the C++ engine to N Python agents.
- [x] Live web dashboard (`dashboard/`), reading the simulation's SQLite database read-only.
- [ ] Order-book-driven trade pricing (see Known Limitations above).
- [ ] Wire up and validate `prod` (live stdin) mode.
- [ ] Train and expose the neural-net strategy through the CLI.

## Disclaimer

This project is developed strictly for academic and educational purposes. It does not constitute financial advice, nor is it designed to reflect actual live-market trading conditions.

If you wish to discuss this project, feel free to reach out via my academic email address listed on my GitHub profile.