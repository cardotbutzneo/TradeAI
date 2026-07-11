#!/bin/bash

# Configuration des chemins vers les scripts Python et c++
MAIN_SCRIPT="src_python/main.py"
GENERATOR_SCRIPT="src_python/data_generator.py"

# Fonction d'aide
usage() {
    echo "Usage :"
    echo "  $0 help [command_name || all]"
    echo "  $0 --generate [file=...] [fdate=...] [dur=...]"
    echo "  $0 --train [file_path] [fast=--fast]"
    echo "  $0 --prod"
    echo "  $0 --clean"
    exit 1
}

help() {
    if [ $# -eq 0 ]; then 
        echo "Error : help() needs at least one argument"
        usage
    fi

    local mode=$1
    if [[ -z "$mode" ]]; then
        echo "Error : help() does not support null input."
        echo "Usage: $0 help [command || all]"
        echo "Use 'train' for help about --train or --prod" 
        exit 1
    fi

    if [[ "$mode" == "all" ]]; then
        if [ -d "help" ]; then
            tail -n +1 help/*
        else
            usage
        fi
    elif [[ "$mode" == "usage" ]]; then
        usage
    else
        mode+=".md"
        if [ -f "help/$mode" ]; then
            tail -n +1 "help/$mode"
            echo ""
        else
            echo "Error : No help found for command '$mode'"
            echo "List of available help commands : "
            if [ -d "help" ]; then
                ls "help/"
            else
                echo "  (No 'help/' directory found)"
            fi
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
        FAST=${2:-""} 
        
        if [[ "$COMMAND" == "--train" ]]; then
            if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
                echo "Error: '${FILE:-"NULL"}': No such file or directory"
                echo "Warning: please make sure that every file needed for the project exists."
                exit 1
            fi
            if [ ! -s "$FILE" ]; then
                echo "Warning: '$FILE' is empty."
                printf "Do you still want to continue? [y/N]: "
                read -r conf
                if [[ "$conf" != "y" ]] && [[ "$conf" != "Y" ]]; then
                    echo "End of the program..."
                    exit 0
                fi  
            fi
        fi
        
        echo "Compiling C++ Engine..."
        if [ -d "src_cpp" ]; then
            cd "src_cpp/" || exit 1
            make
            if [ $? -ne 0 ]; then
                echo "Error: 'make' failed to compile C++ engine. End of the program..."
                exit 1
            fi
            cd ".." || exit 1
        else
            echo "Error: 'src_cpp/' directory not found."
            exit 1
        fi
        
        # Sauvegarde d'état propre (Efface puis ajoute)
        echo "$STDOUT" > .last_run
        if [ -n "$FILE" ]; then
            echo "$FILE" >> .last_run
        fi
        
        echo "Running simulation..."
        python3 "$MAIN_SCRIPT" "$COMMAND" "$FILE" "$FAST" 2> "$STDOUT"
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
                    echo "Unknown argument for --generate : $1"
                    usage
                    ;;
            esac
            shift 
        done

        mkdir -p "$(dirname "$OUT_FILE")"
        echo "$OUT_FILE" > .last_run

        echo "Generating market data into $OUT_FILE..."
        python3 "$GENERATOR_SCRIPT" "${PY_ARGS[@]}" 1> "$OUT_FILE"
        ;;

    *)
        echo "Command $COMMAND not found"
        usage
        ;;
esac