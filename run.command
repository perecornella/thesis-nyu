#!/bin/bash
echo "Starting the program..."

# Get the directory where the .command file is stored
script_dir="$(cd "$(dirname "$0")" && pwd)"
cd $script_dir

source "./venv/bin/activate"

# Prompt for a directory
echo "If desired, enter a specific directory (or press Enter to skip):"
read input_directory

if [[ -n "$input_directory" ]]; then
    echo "If desired, enter a specific file (or press Enter to skip):"
    read input_file
	python3 "enrich_dataset.py" $input_directory $input_file 	
else
    python3 "enrich_dataset.py" $input_directory
fi

echo "Program finished!"