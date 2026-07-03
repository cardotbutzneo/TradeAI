# TradeAI

## Overview
TradeAI is an educational project designed to explore fundamental concepts of **quantitative finance**, **inter-process communication (IPC)**, and **applied mathematics**.

The goal of this project is to build a high-performance market simulator in C++ linked with an algorithmic trading agent in Python. The architecture is designed to evolve progressively as new systems and software engineering concepts are implemented.

## Project Structure
The project is split into three main architectural components:

1. **Market Simulation Engine (C++)** - Discrete-time price evolution modeling.
   - Order-book dynamics and volumetric impact modeling (Slippage/Malus).
   - Multi-asset market environment orchestration.

2. **Algorithmic Trading Agent (Python)** - Quantitative trading strategies (signals, basic technical analysis).
   - Portfolio state tracking and risk-tolerance validation.

3. **Data Analysis & Analytics** - Historical tick-data serialization.
   - Performance visual analytics (equity curves, asset tracking).

## Requirements
To compile and run this project, you need a **C++11 (or higher) compiler (g++)**, **Python 3.9+**, and the following packages:

- `numpy`
- `matplotlib`

## Setup

It is highly recommended to use an isolated Python **virtual environment**.

### 1. Initialize the Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate     # Windows
````

### Install Dependencies
````bash
pip install -r requirements.txt
````

## Run the simulation
### Generate Data (optional)
To bootstrap the backtester with synthetic or historical data, generate a CSV file:
````
cd src_python/
python3 data_generator.py > ../data/historic.csv
````
Note: If you modify the target location of the CSV, make sure to update the file path bindings inside `main.cpp` before recompiling.
### Execute the pipeline
Because the C++ engine and the Python agent communicate in real-time via standard streams (IPC Pipes), standard debug logs are routed to stderr. Execute the pipeline by running:
````
cd src_python/
python3 main.py 2> bourse.log
````
### Execution mode 
The binary engine supports two operational modes:
- `--train (Default)`: Backtests the Python agent against historical/static CSV data streams.
- `--prod` : Switches to a dynamic, live broker simulation where prices update interactively based on agent execution volume.

Note: The CLI argument parser layer is currently under active R&D.

### Roadmap & Expected Changes
- [ ] Asynchronous Networking: Migrate from synchronous IPC Pipes to a multi-client network layer using WebSockets in C++.
- [ ] Advanced Market Impact: Implement a full Limit Order Book (LOB) to replace mathematical proxy formulas.
- [ ] Web Dashboard: Integrate a real-time tracking interface built with JavaScript.

## Disclaimer

This project is developed strictly for academic and educational purposes. It does not constitute financial advice, nor is it designed to reflect actual live-market trading conditions.

If you wish to discuss this project, feel free to reach out via my academic email address listed on my GitHub profile.
