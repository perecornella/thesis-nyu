🚀 If your computer supports Bash scripting (e.g., Linux, macOS, or Windows with a Bash shell installed), you can simply double-click run.command to execute the program. Ensure the script has executable permissions (chmod +x run.command on Unix-like systems) before running.

**⚙️ Instructions to set up the GUI**
1. Make sure you have the last version of the repo.
2. Set up a python virtual environment ```python3 -m venv ./venv``` (change python3 to your interpreter).
3. Activate the virtual environment ```source ./venv/bin/activate```.
4. Install the packages ```pip3 install -r ./config/requirements.txt``` (change pip3 to your downloader).
6. Run ```crawl.py <username> v0```.
   
   ⚠️ Running this twice will erase your progress.

**🚘 Instructions to run the GUI**

```python3 -m widget.py <username> v0``` opens the non-explored file according to *progress.csv*.

```python3 -m widget.py <username> v0 <input_directory>``` opens the first non-explored file in *input_directory* according to *progress.csv*.

```python3 -m widget.py <username> v0 <input_directory> <filename>``` opens the file in *input_directory/filename*. Running in this mode won't let you save the form.

**💁🏻‍♂️ Information**

The widget can be used to navigate through files and to submit conclusions extracted from them. By default will show the frequency response area (FRA) of a recording and the traces corresponding to the best frequency. It is possible to switch to a visualization that shows all the traces. And to switch between the different datachannels of the recording. 
The submissions will be stored in the metadata folder and will contain 

 - Directory
 - Filename

And values the user considers
 - Tuned: if there is a clear region of frequencies to which the recording site was more responsive (Yes / No)
 - Clear: if there is no noise outside of the best frequencies (Yes / No)
 - Exemplar: if the file remarcably shows the profile of the recording site  (Yes / No)
 - Type: if the voltage traces indicate the type of recording (Intracellular / Extracellular)
 - Coordinates: known coordinates of the recording site (x,y,z)
