Pere Cornellà - 12/12/2024

**⚙️ Instructions to set up the GUI**
1. Make sure you have the last version of the repo.
2. Set up a python virtual environment ```python3 -m venv ./venv``` (change python3 to your interpreter).
3. Activate the virtual environment ```source ./venv/bin/activate```.
4. Install the packages ```pip3 install -r ./config/requirements.txt``` (change pip3 to your downloader).
6. Run ```crawl.py <username>```.
   
   ⚠️ Running this twice will erase your progress.

**🚘 Instructions to run the GUI**

```python3 -m widget.py <username>``` opens the non-explored file according to *progress.csv*.

```python3 -m widget.py <username> <input_directory>``` opens the first non-explored file in *input_directory* according to *progress.csv*.

```python3 -m widget.py <username> <input_directory> <filename>``` opens the file in *input_directory/filename*. Running in this mode won't let you save the form.

**💁🏻‍♂️ Information**

The widget can be used to analize and input metadata. By default will show the frequency response area (FRA) of a recording and the traces corresponding
to the best frequency. It is possible to switch to a visualization that shows all the traces. The default values in the form are suggested using numerical calculations.
The metadata will consist of fixed values

 - Directory
 - Filename

And values the user can modify
 - Tuned (Yes / No)
 - Clear (Yes / No)
 - Healthy (Yes / No)
 - Type (Intracellular / Extracellular)
 - Relative coordinates (x,y,z)
