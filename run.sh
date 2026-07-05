#!/bin/bash

# Configuration des chemins vers les scripts Python
MAIN_SCRIPT="src_python/main.py"
GENERATOR_SCRIPT="src_python/data_generator.py"
HELP_DIRECTORY="help/*"

# Fonction d'aide
usage() {
    local mode=${1:-"all"}
    case "$mode" in
        "generate")
            if [ -f "help/generate" ]; then
                cat "help/generate"
            else
                echo "Usage: $0 [--generate [file=...] [fdate=...] [ldate=...]]"
            fi
            ;;
        "run")
        ;;
        *)
            echo "Usage :"
            echo "  $0 help [command_name || all]"
            echo "  $0 --generate [file=...] [fdate=...] [ldate=...]"
            echo "  $0 --train [file_path]"
            echo "  $0 --prod"
            echo "  $0 --clean"
            ;;
    esac
    exit 1
}

help() {
    if [ $# -eq 0 ]; then 
        echo "Error : help() needs at least one argument"
        usage
    fi

    if [[ $1 == "" ]]; then
        echo "help() do not support null input."
        echo "usage: help [command || all]"
        echo "use 'run' for help about --train or --prod" 
        exit 1
    fi

    local mode=$1
    if [[ "$mode" == "all" ]]; then
        if [ -d "help" ]; then
            tail -n +1 help/*
        else
            usage
        fi
    elif [[ "$mode" == "usage" ]]; then
        usage
    else
        if [ -f "help/$mode" ]; then
            tail -n +1 "help/$mode"
        else
            echo "Error : No help found for command '$mode'"
            echo "List of available command : "
            ls "help/"
            exit 1
        fi
    fi
}

# Si aucun argument n'est fourni, on affiche l'aide
if [ $# -eq 0 ]; then
    echo "Cannot run the script : need at least one argument"
    usage
fi

COMMAND=$1
shift

case "$COMMAND" in
    help)
        help "${1:-""}"
        ;;
        
    --clean)
        echo "Cleaning C++ binaries..."
        if [ -d "src_cpp" ]; then
            cd "src_cpp/" || exit 1
            make clean > /dev/null
            cd ".." || exit 1
        fi
        
        if [ -f .last_run ]; then
            echo "Cleaning generated simulation files..."
            while read -r file; do
                if [ -f "$file" ]; then
                    rm "$file"
                    echo "$file removed."
                fi
            done < .last_run
            rm .last_run
            echo "Project successfully cleaned!"
        else
            echo "Nothing to clean : all done."
        fi
        ;;
        
    --train|--prod)
        STDOUT="src_cpp/bourse.log"
        FILE=${1:-""}
        
        if [[ "$COMMAND" == "--train" ]]; then
            if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
                echo "Error: '${FILE:-"NULL"}': No such file or directory"
                echo "Warnig: please make sur that every file needed for the projet exist"
                exit 1
            fi
            if [ ! -s "$FILE" ]; then
                echo "Warning: '$FILE' is empty."
                echo "Do you still want to continue ? [y/n]"
                read -r conf
                if [[ "$conf" == "n" ]] || [[ -z "$conf" ]] ; then
                    echo "End of the programm..."
                    exit 0
                fi  
            fi
        fi
        
        echo "Compiling C++ Engine..."
        cd "src_cpp/" || exit 1
        make
        cd ".." || exit 1
        
        echo "$STDOUT" > .last_run
        if [ -n "$FILE" ] && [ "$FILE" != "null" ]; then
            echo "$FILE" >> .last_run
        fi
        
        echo "Running simulation..."
        python3 "$MAIN_SCRIPT" "$COMMAND" "$FILE" 2> "$STDOUT"
        ;;

    --generate)
        OUT_FILE="data/historic.csv"
        PY_ARGS=()

        while [ $# -gt 0 ]; do
            case "$1" in
                file=*)
                    OUT_FILE="${1#*=}"
                    ;;
                fdate=*)
                    PY_ARGS+=("fdate" "${1#*=}")
                    ;;
                dur=*)
                    PY_ARGS+=("dur" "${1#*=}")
                ;;
                *)
                    echo "Unknow argument for --generate : $1"
                    usage "generate"
                    ;;
            esac
            shift 
        done

        mkdir -p "$(dirname "$OUT_FILE")"

        echo "$OUT_FILE" > .last_run

        echo "Generating market data into $OUT_FILE..."
        echo "python3 "$GENERATOR_SCRIPT" "${PY_ARGS[@]}" 1> "$OUT_FILE""
        python3 "$GENERATOR_SCRIPT" "${PY_ARGS[@]}" 1> "$OUT_FILE"
        ;;

    *)
        echo "Command $COMMAND not found"
        usage
        ;;
esac