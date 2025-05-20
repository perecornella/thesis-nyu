#!/bin/bash

version=v4

script_dir="$(cd "$(dirname "$0")" && pwd)"
cd $script_dir

# Get the user
user=$(whoami)

# Set where to store the logs
log_dir="users/$user/logs/$version"
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

shape=all # [all, ...]
channel=all # [all, di0P, di1P, di2P, di3P]
mean=all # [all, zeromean, other]
symmetry=all # [all, asymmetric, symmetric]
python3 "filter.py" $user $version $shape $channel $mean $symmetry
python3 "gui.py" $user $version $shape $channel $mean $symmetry

echo "Program finished!"

exit