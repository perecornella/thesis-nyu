#!/bin/bash
user=$(whoami)
echo "Starting the program as $user..."

# Get the directory where the .command file is stored
script_dir="$(cd "$(dirname "$0")" && pwd)"
cd $script_dir

# Create / activate the venv install the dependencies and create the metadata folder
if [ ! -d "venv" ]; then
    python3 -m venv ./venv
fi
source "./venv/bin/activate"
pip3 install -r "./config/requirements.txt" > /dev/null 2>&1
if [ ! -d "metadata/$user" ]; then
    python3 "crawl.py" $user 
fi

# Prompt for a directory
echo "If desired, enter a specific directory (or press Enter to skip):"
read input_directory
if [[ -n "$input_directory" ]]; then
    echo "If desired, enter a specific file (or press Enter to skip):"
    read input_file
    if [[ -n "$input_file" ]]; then
	    python3 "widget.py" $user $input_directory $input_file 	
    else
        python3 "widget.py" $user $input_directory
    fi
else
    python3 "widget.py" $user
fi

echo "Program finished!"