# 🚀 Getting Started (A to Z)

A **step-by-step** guide to run TradeAI from scratch.
Every command is explained, so you know what it does *before* running it.

> **One-line summary:** the project targets **Linux**. On Windows, use **WSL**
> (a Linux environment built into Windows), install the tools, then run
> everything through the `run.sh` script.

---

## 1. Why WSL instead of plain Windows?

The project mixes two worlds:

- A **C++ engine** that must be **compiled** with `g++` + `make` (Linux tools).
- A **`run.sh` orchestration script** written in **Bash** (the Linux shell).

PowerShell / the Windows prompt cannot run those natively. **WSL** (Windows
Subsystem for Linux) gives you a real Linux inside Windows, which is the
simplest path. Everything in this guide happens **inside a WSL terminal**.

> Open WSL: Windows key → type **"Ubuntu"** or **"wsl"** → Enter.
> You should see a prompt like:
> `user@PC:/mnt/c/...$`

---

## 2. Install the tools (do this **once**)

```bash
# Update the package list, then install:
#  - build-essential : the C++ compiler (g++) and make
#  - python3-pip     : pip, to install Python packages
sudo apt update && sudo apt install -y build-essential python3-pip
```

`sudo` asks for your **WSL password** (the one set when Ubuntu was installed).
The password stays hidden while typing — that's normal.

Check everything is present:

```bash
g++ --version && make --version && python3 --version
```

You should see three version numbers, no errors.

---

## 3. Go to the project folder

The project lives on your Windows drive, reachable from WSL via `/mnt/c/...`:

```bash
cd /mnt/c/Users/X515/Documents/GitHub/TradeAI
```

> `cd` = *change directory*.

---

## 4. Install the Python dependencies (do this **once**)

```bash
# Installs numpy, matplotlib and websockets listed in requirements.txt.
# --break-system-packages : bypasses Ubuntu's "externally-managed" block.
pip install --break-system-packages -r requirements.txt
```

> `requirements.txt` lists the 3 required packages. The rest (asyncio, math…)
> already ships with Python.

---

## 5. Generate market data

The engine needs a CSV price file. We build one with a simulator
(Geometric Brownian Motion = a realistic random price curve).

```bash
# dur=1   -> 1 trading day (~100 points, ideal for a quick test)
# file=.. -> where to write the generated file
./run.sh --generate dur=1 file=data/small.csv
```

Check the file was created:

```bash
wc -l data/small.csv    # prints the number of lines (must be > 0)
```

> For a bigger, more realistic dataset: `./run.sh --generate dur=7 file=data/historic.csv`
> (7 days). But it takes longer to simulate (see the `--fast` note below).

---

## 6. Run the simulation 🎯

```bash
./run.sh --train data/small.csv
```

What this command does, in order:

1. **Compiles** the C++ engine (`make`) → creates the `src_cpp/main` binary.
2. **Launches** `main.py`, which starts:
   - the **broker** (the conductor between C++ and the agents),
   - **3 trading agents** (wallets of 1000€, 2000€, 500€).
3. C++ streams prices tick by tick, the agents buy/sell.

⏱️ With `dur=1` it takes **~20 seconds**. The terminal stays quiet — that's
normal: **all the detail goes into a log file**, not the screen.

---

## 7. See what's happening (logs)

All activity (broker, agents, C++) is written to `src_cpp/bourse.log`.

**While** it runs, open a **2nd WSL terminal** and follow it live:

```bash
cd /mnt/c/Users/X515/Documents/GitHub/TradeAI
tail -f src_cpp/bourse.log     # live scroll ; Ctrl+C to stop following
```

**After** the run, verify it worked:

```bash
grep "Fin. Wallet" src_cpp/bourse.log       # final wallets of the 3 agents
grep -c "TICK;"    src_cpp/bourse.log        # number of ticks processed (must be > 0)
grep -iE "Traceback|Error" src_cpp/bourse.log    # should print NOTHING
```

✅ **If it works**, you'll see 3 `Fin. Wallet` lines with amounts **different**
from 1000/2000/500 → proof the agents actually traded.

---

## 8. Clean up (optional)

```bash
./run.sh --clean    # removes the compiled binary and generated files
```

---

## 🆘 Common problems (the ones you may hit)

| Error message | Cause | Fix |
|---|---|---|
| `./run.sh: cannot execute: required file not found` | `run.sh` has Windows line endings (CRLF) | Handled by `.gitattributes`. Otherwise: `sed -i 's/\r$//' run.sh` |
| `pip: command not found` | pip not installed | `sudo apt install python3-pip` |
| `externally-managed-environment` | Ubuntu blocks pip by default | Add `--break-system-packages` to the pip command |
| `No such file or directory: './src_cpp/main'` | The C++ engine was not compiled | Use `./run.sh --train ...` (it compiles), not `python3 main.py` directly |
| `Fichier introuvable` (in the log) | No data file passed to C++ | Always pass a file: `./run.sh --train data/small.csv` |
| `python: command not found` | On Linux it's `python3` | Use `python3`, never `python` |

---

## ⚠️ Important: do NOT use `--fast`

The `--fast` flag removes the pause between ticks on the C++ side. But the whole
synchronization relies on that pause: without it, the engine finishes **before**
receiving the agents' orders → **deadlock**.

👉 Run **without** `--fast` until that bug is fixed.

---

## 📋 Quick recap

```bash
# --- Once ---
sudo apt update && sudo apt install -y build-essential python3-pip
cd /mnt/c/Users/X515/Documents/GitHub/TradeAI
pip install --break-system-packages -r requirements.txt

# --- Every time ---
./run.sh --generate dur=1 file=data/small.csv   # 1) generate data
./run.sh --train data/small.csv                 # 2) run the simulation
grep "Fin. Wallet" src_cpp/bourse.log           # 3) check the result
```
