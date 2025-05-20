import pandas as pd
import time
import sys
import os

def crawl_database(root_dir: str):

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

    dir_info = pd.DataFrame(columns=['directory', 'non checked files', 'checked files', 'error files'])
    
    for folder in list_of_folders:
        non_checked_files = []
        for file_name in os.listdir(root_dir + folder):
            if file_name.startswith('A') and file_name[-3] == "d":
                non_checked_files.append(file_name[0:-3])
    
        info = {'directory': folder,
                'non checked files': sorted(non_checked_files),
                'checked files': [],
                'error files': []}
        
        dir_info = dir_info._append(info, ignore_index = True)

    dir_info = dir_info.sort_values(by=['directory'], ascending=True)
    
    return dir_info

def create_progress_file(root_dir: str, shape, channel, mean, symmetry):

    file_info = pd.read_csv(root_dir + "Pere/metadata/file_info.csv")

    if channel != 'all':
        file_info = file_info[file_info['channel'] == channel]
    if shape != 'all':
        file_info = file_info[(file_info['shape'] == f'({shape[0:2]}x{shape[3]})')]    
    if mean != 'all':
        file_info['mean_category'] = file_info['mean'].apply(lambda x: 'zeromean' if -2 < x < 2 else 'other')
        file_info = file_info[file_info['mean_category'] == mean]
    if symmetry != 'all':
        threshold = 0.5
        file_info['symmetry'] = file_info.apply(
            lambda x: 'asymmetric' if abs(abs(x['mean'] - x['max']) - abs(x['mean'] - x['min'])) > threshold else 'symmetric', axis=1
        )
        file_info = file_info[file_info['symmetry'] == symmetry]

    annotations = pd.read_csv(root_dir + "Pere/metadata/annotations.csv")
    annotations = annotations.merge(file_info[['directory', 'filename', 'channel']], on=['directory', 'filename', 'channel'], how='inner')
    progress = pd.DataFrame(columns=['directory', 'non checked files', 'checked files', 'error files'])
    
    annotations = annotations[['directory', 'filename']].drop_duplicates()
    file_info = file_info[['directory', 'filename']].drop_duplicates()

    for directory in file_info['directory'].unique():
        directory_files = file_info[file_info['directory'] == directory]['filename'].tolist()
        checked_files = annotations[annotations['directory'] == directory]['filename'].tolist()
        non_checked_files = [f for f in directory_files if f not in checked_files]
        
        info = {
            'directory': directory,
            'non checked files': sorted(non_checked_files),
            'checked files': sorted(checked_files),
            'error files': [] 
        }
        progress = progress._append(info, ignore_index=True)
    
    progress = progress.sort_values(by=['directory'], ascending=True)
    
    return progress


if __name__ == "__main__":

    user = sys.argv[1]
    shape, channel, mean, symmetry = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]

    if user == "perecornella":
        root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
        progress_path = root_dir + f'Pere/metadata/progress/{shape}_{channel}_{mean}_{symmetry}_progress.csv'
        annotations_path = root_dir + f'Pere/metadata/annotations.csv'
        discarded_path = root_dir + f'Pere/metadata/progress/{shape}_{channel}_{mean}_{symmetry}_discarded.csv'

    elif user == "ar65":
        root_dir = "/Users/ar65/Library/CloudStorage/GoogleDrive-ar65@nyu.edu/My Drive/ReyesLabNYU/"
        progress_path = root_dir + f'Pere/metadata/progress/{shape}_{channel}_{mean}_{symmetry}_progress.csv'
        annotations_path = root_dir + f'Pere/metadata/annotations.csv'
        discarded_path = root_dir + f'Pere/metadata/progress/{shape}_{channel}_{mean}_{symmetry}_discarded.csv'

    else:
        root_dir = "./toy_dataset/"
        if not os.path.exists(root_dir + 'metadata/progress/'):
            os.makedirs(root_dir +  'metadata/progress/')
        progress_path = root_dir + f'metadata/progress/{shape}_{channel}_{mean}_{symmetry}_progress.csv'

    try:
        pd.read_csv(progress_path)
    except FileNotFoundError:
        if user == "perecornell" or user ==  "ar65":
            progress = create_progress_file(root_dir, shape, channel, mean, symmetry)
        else:
            progress = crawl_database(root_dir)
        progress.to_csv(progress_path, index=False)