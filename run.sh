#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON=$(command -v python3 || command -v python || true)
if [ -z "$PYTHON" ]; then
    echo "Python 3 is required but not found in PATH." >&2
    exit 1
fi

MAIN_MODULE="src_python.cli"
DATA_GENERATOR_MODULE="src_python.data_generator"
LOG_DIR="logs"
CONFIG_DIR="config"
CONFIG_FILE="settings.json"
DEFAULT_OUTPUT_LOG="${LOG_DIR}/simulation.log"
DEFAULT_ERROR_LOG="${LOG_DIR}/error.log"

usage() {
    cat <<EOF
Usage:
  $0 help [command|all]
  $0 --generate [--file OUT] [--fdate YYYY-MM-DD] [--dur DAYS]
  $0 --train FILE [--fast] [--clients N]
  $0 --prod [--fast] [--clients N]
  $0 --clean [all]
EOF
    exit 1
}

ensure_config() {
    if [ ! -f "${CONFIG_DIR}/${CONFIG_FILE}" ]; then
        mkdir -p "$CONFIG_DIR"
        cat > "${CONFIG_DIR}/${CONFIG_FILE}" <<EOF
{
  "debug-mode": false,
  "output-file": "${DEFAULT_OUTPUT_LOG}",
  "error-file": "${DEFAULT_ERROR_LOG}"
}
EOF
    fi
}

clean_all() {
    echo "Cleaning build artifacts and generated files..."
    if [ -d "src_cpp" ]; then
        (cd "src_cpp" && make clean)
    fi
    rm -rf "${LOG_DIR}" .last_run data/*
    if [ ! -z "$1" ] && [ "$1" == "all" ]; then
        rm -rf "${CONFIG_DIR}"
    fi
    echo "Clean complete."
}

if [ $# -eq 0 ]; then
    usage
fi

COMMAND=$1
shift
ensure_config

case "$COMMAND" in
    help)
        $PYTHON -m $MAIN_MODULE -h
        ;;

    --clean)
        if [ $# -gt 1 ]; then
            echo "Usage: $0 --clean [all]" >&2
            exit 1
        fi
        if [ "${1:-}" = "all" ]; then
            clean_all all
        else
            clean_all
        fi
        ;;

    --generate)
        OUT_FILE="data/historic.csv"
        FDATE=""
        DUR=7

        while [ $# -gt 0 ]; do
            case "$1" in
                --file=*) OUT_FILE="${1#*=}" ;;
                --fdate=*) FDATE="${1#*=}" ;;
                --dur=*) DUR="${1#*=}" ;;
                *)
                    echo "Unknown argument for --generate: $1" >&2
                    usage
                    ;;
            esac
            shift
        done

        mkdir -p "$(dirname "$OUT_FILE")"
        echo "Generating market data into $OUT_FILE..."
        if [ -n "$FDATE" ]; then
            "$PYTHON" -m "$DATA_GENERATOR_MODULE" --fdate "$FDATE" --dur "$DUR" > "$OUT_FILE"
        else
            "$PYTHON" -m "$DATA_GENERATOR_MODULE" --dur "$DUR" > "$OUT_FILE"
        fi
        echo "$OUT_FILE" > .last_run
        ;;

    train|prod)
        if [ "$COMMAND" = "train" ] && [ $# -eq 0 ]; then
            echo "Error: train requires a data file." >&2
            usage
        fi

        FILE=""
        FAST=()
        CLIENTS=3

        if [ "$COMMAND" = "train" ]; then
            FILE=$1
            shift
            if [ ! -f "$FILE" ]; then
                echo "Error: File '$FILE' does not exist." >&2
                exit 1
            fi
        fi

        while [ $# -gt 0 ]; do
            case "$1" in
                --fast)
                    FAST=("--fast")
                    ;;
                --clients)
                    shift
                    if [ $# -eq 0 ]; then
                        echo "Error: --clients requires a numeric argument." >&2
                        exit 1
                    fi
                    CLIENTS="$1"
                    ;;
                *)
                    echo "Unknown option: $1" >&2
                    usage
                    ;;
            esac
            shift
        done

        mkdir -p "$LOG_DIR"

        if [ -d "src_cpp" ]; then
            echo "Compiling C++ engine..."
            (cd "src_cpp" && make)
        fi

        echo "$DEFAULT_ERROR_LOG" > .last_run
        if [ -n "$FILE" ]; then
            echo "$FILE" >> .last_run
        fi

        echo "Running simulation in $COMMAND mode..."
        echo "$PYTHON" -m "$MAIN_MODULE" "$COMMAND" "$FILE" "${FAST[@]}" --clients "$CLIENTS"
        "$PYTHON" -m "$MAIN_MODULE" "$COMMAND" "$FILE" "${FAST[@]}" --clients "$CLIENTS"
        ;;

    *)
        echo "Unknown command: $COMMAND" >&2
        usage
        ;;
esac
