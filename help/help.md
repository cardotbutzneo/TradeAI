===================================================================
 HELP: General Manual
===================================================================
This folder is a hand-written manual for run.sh. Note that
`./run.sh help` itself does not print these files: it just forwards
to the Python CLI's own `-h` output (src_python/cli.py, train/prod
arguments only). Read the file below that matches what you need.

Usage:
  ./run.sh help

Commands available:
  --generate : Generate synthetic historical market data.
               -> see generate.md
  train/prod : Run the simulation (train = historical file,
               prod = live stdin feed, WIP).
               -> see run.md
  --clean    : Remove temporary logs, generated data and compiled
               C++ binaries.
               -> see clean.md
===================================================================
