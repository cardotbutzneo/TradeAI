# TradeAI

## Overview
TradeAI is an educational project designed to explore fundamental concepts of **quantitative finance**, **inter-process communication (IPC)**, and **applied mathematics**.

The goal of this project is to build a high-performance market simulator in C++ linked with an algorithmic trading agent in Python. The architecture is designed to evolve progressively as new systems and software engineering concepts are implemented.

## Project Structure
The project is split into two main architectural components:

1. **Market Simulation Engine (C++)** - Discrete-time price evolution modeling.
   - Order-book dynamics and volumetric impact modeling (Slippage/Malus).
   - Multi-asset market environment orchestration.

2. **Algorithmic Trading Agent (Python)** - Quantitative trading strategies (signals, basic technical analysis).
   - Portfolio state tracking and risk-tolerance validation.

## Requirements
To compile and run this project, you need a **C++11 (or higher) compiler (g++)**, **Python 3.9+**, and the following packages:

- `numpy`
- `matplotlib` (optional: for performance visualization)
- `websockets`
- `asyncho`

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
The project includes an orchestrator Bash script `run.sh` to manage compilation, data generation, and execution.
### General usage
````bash
./run.sh [command || help] 
````
### Available commands
- `./run.sh --generate [file=...] [fdate=...] [dur=...]`: Triggers the Python data generator engine to build historical synthetic market ticks.
- `./run.sh --train [file_path] [fast=--fast]`: Compiles the C++ core engine on the fly and runs the simulation training loop over a data file.
- `./run.sh --clean`: Cleans up all local temporary logs, .last_run persistence states, and compiled C++ binaries.
- `./run.sh help [command || all]`: Print the usage manual for this command. If all is used as a parameter, print all the help file available.  

## Known Issues & Current Limitations
### WebSocket Connectivity (Work in Progress)
* Status: The core communication currently relies on stable, synchronous IPC pipelines orchestrated via Bash.

* Bug (Issue #1): The prototype multi-client network layer built with WebSockets suffers from premature disconnection. The Python agent receives a WebSocket close with code 1001.

### Roadmap & Expected Changes
- [x] Asynchronous Networking: Migrate from synchronous IPC Pipes to a multi-client network layer using WebSockets in C++.
- [ ] Advanced Market Impact: Implement a full Limit Order Book (LOB) to replace mathematical proxy formulas.
- [ ] Web Dashboard: Integrate a real-time tracking interface built with JavaScript.

## Disclaimer

This project is developed strictly for academic and educational purposes. It does not constitute financial advice, nor is it designed to reflect actual live-market trading conditions.

If you wish to discuss this project, feel free to reach out via my academic email address listed on my GitHub profile.
