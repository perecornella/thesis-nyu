from utils import read_in_data
import os
import pandas as pd
import numpy as np
import time
import sys


user = sys.argv[1]
if user == "perecornella":
    root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
elif user == "alex":
    root_dir = ""
else:
    root_dir = "toy_dataset/"

list_dir = []
for dir in os.listdir(root_dir):
    if dir == 'in_vivo_data_pw':
        for dir_aux in os.listdir(root_dir + dir):
            if dir_aux[0] == str(1):
                list_dir.append(dir+'/'+dir_aux+'/')
    elif dir[0] == str(1):
        list_dir.append(dir + '/')
    else:
        pass

dir_info = pd.DataFrame(columns=['name', 'start', 'end', 'checkpoint'])
measure1 = time.time()
for dir in list_dir:
    Match = np.zeros(1001)
    min_file = 1001
    max_file = 0

    for file in os.listdir(root_dir + dir):
        if file[0] == 'A':
            num = int(file[1:-3])
        
        if num > max_file:
            max_file = num
        if num < min_file:
            min_file = num
   
        # if Match[num] == 0:
        #     Match[num] = 1
        # elif Match[num] == 1:
        #     Match[num] = 0
   
    info = {'name': dir,
            'start': min_file,
            'end': max_file,
            'checkpoint': min_file} # 'Match': np.where(Match == 1)}
    dir_info = dir_info._append(info, ignore_index = True)

measure2 = time.time()
print('Your dataset was crawled in', round(measure2 - measure1,2), 'seconds.')

if not os.path.exists(f'./metadata/{user}'):
    os.makedirs(f'./metadata/{user}')

dir_info.to_csv(f'./metadata/{user}/progress.csv', index=False)