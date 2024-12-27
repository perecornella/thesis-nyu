#!/bin/bash

version=v0

script_dir="$(cd "$(dirname "$0")" && pwd)"
cd $script_dir

# Get the user
user=$(whoami)

# Set where to store the logs
log_dir="logs/$user/$version"
if [ ! -d "$log_dir" ]; then
    mkdir -p "$log_dir"
fi
log_file="$log_dir/$(date +'%Y-%m-%d_%H-%M-%S').log"
exec > >(tee -a "$log_file") 2>&1

echo "Starting the program as $user..."

# Update / activate the venv install the dependencies
if [ ! -d "venv/$version" ]; then
    python3 -m venv ./venv/$version
fi
find venv -mindepth 1 -maxdepth 1 ! -name "$version" -exec rm -rf {} +
source "./venv/$version/bin/activate"
pip3 install -r "./config/requirements.txt" > /dev/null 2>&1

# Create the metadata folder
metadata_dir="metadata/$user/$version"
if [ ! -d "$metadata_dir" ]; then
    mkdir -p "$metadata_dir"
    python3 "crawl.py" $user $version
fi

# Prompt for a directory
echo "If desired, enter a specific directory (or press Enter to skip):"
read input_directory
if [[ -n "$input_directory" ]]; then
    echo "If desired, enter a specific file (or press Enter to skip):"
    read input_file
    if [[ -n "$input_file" ]]; then
        echo "Launching at $input_directory$input_file."
	    python3 "widget.py" $user $version $input_directory $input_file 
    else
        echo "Launching at $input_directory."
        python3 "widget.py" $user $version $input_directory
    fi
else
    python3 "widget.py" $user $version
fi

echo "Program finished!"

exit