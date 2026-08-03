===================================================================
 HELP: --clean
===================================================================
Usage:
  ./run.sh --clean [all]

Behavior:
  * Runs `make clean` in src_cpp/ (removes obj/ and the compiled
    'main' binary).
  * Removes the logs/ directory, the .last_run marker file, and
    every file under data/.
  * With the optional 'all' argument, also removes the config/
    directory. It is regenerated automatically (with default values)
    the next time run.sh runs.

Note:
  This does not touch data/trading.db's history on its own — it is
  inside data/, so a plain `./run.sh --clean` deletes it too.
===================================================================
