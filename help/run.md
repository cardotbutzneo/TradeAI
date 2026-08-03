===================================================================
 HELP: train | prod
===================================================================
Usage:
  ./run.sh train FILE [--fast] [--clients N]
  ./run.sh prod [--fast] [--clients N]

Arguments:
  FILE        : Filepath of the input historical CSV (train mode
                only, required). Typically the output of --generate.
  --fast      : Removes the 100ms delay the C++ engine adds between
                ticks. (Default: delay applied)
  --clients   : Number of AI agents to launch in parallel, each with
                its own strategy and wallet.
                (Default: 3)

What happens:
  1. The C++ engine (src_cpp) is (re)compiled.
  2. The Python broker starts it as a subprocess and opens two
     WebSocket servers (ticks on :8765, orders on :8766).
  3. --clients AI agents connect, register, and trade tick by tick
     until the engine prints "STOP".
  4. Every tick, trade and agent outcome is recorded in
     data/trading.db (see src_python/dataBase.py). Run
     `python3 dashboard/app.py` in another terminal to watch it live.

Warning:
  'prod' streams data over stdin instead of reading a file, but this
  mode is still WORK IN PROGRESS. Please use 'train' for now.
===================================================================
