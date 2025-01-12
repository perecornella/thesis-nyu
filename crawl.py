from utils import read_in_data
import os
import pandas as pd
import numpy as np
import time
import sys

user = sys.argv[1]
if user == "perecornella":
    root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
elif user == "ar65":
    root_dir = "/Users/ar65/Library/CloudStorage/GoogleDrive-ar65@nyu.edu/My Drive/ReyesLabNYU/"
else:
    root_dir = "toy_dataset/"

list_of_folders = []
for folder in os.listdir(root_dir):
    if folder == 'in_vivo_data_pw':
        for dir_aux in os.listdir(root_dir + folder):
            if dir_aux[0] == str(1):
                list_of_folders.append(f"{folder}/{dir_aux}/")
    elif folder[0] == str(1):
        list_of_folders.append(f"{folder}/")
    else:
        pass

dir_info = pd.DataFrame(columns=['name', 'non checked files', 'checked files', 'error files'])
measure1 = time.time()
for folder in list_of_folders:
    non_checked_files = []
    for file_name in os.listdir(root_dir + folder):
        if file_name.startswith('A') and file_name[-3] == "d":
            non_checked_files.append(file_name[0:-3])
   
    info = {'name': folder,
            'non checked files': sorted(non_checked_files),
            'checked files': [],
            'error files': []}
    
    dir_info = dir_info._append(info, ignore_index = True)

dir_info = dir_info.sort_values(by=['name'], ascending=True)
measure2 = time.time()
print('Your dataset was crawled in', round(measure2 - measure1,2), 'seconds.')

dir_info.to_csv(f'./metadata/{user}/progress.csv', index=False)