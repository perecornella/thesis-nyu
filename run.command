#!/bin/bash

# Get the directory where the .command file is stored
script_dir="$(cd "$(dirname "$0")" && pwd)"
cd $script_dir

# Get the user
user=$(whoami)

# Logs
log_dir="logs/$user"
if [ ! -d "$log_dir" ]; then
    mkdir -p "$log_dir"
fi
log_file="$log_dir/$(date +'%Y-%m-%d_%H-%M-%S').log"
exec > >(tee -a "$log_file") 2>&1


echo "Starting the program as $user..."

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
        echo "Launching at $input_directory$input_file."
	    python3 "widget.py" $user $input_directory $input_file
    else
        echo "Launching at $input_directory."
        python3 "widget.py" $user $input_directory 
    fi
else
    python3 "widget.py" $user
fi

echo "Program finished!"

exit 0