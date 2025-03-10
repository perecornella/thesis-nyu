from utils import read_in_data, get_filenames, get_recording_activity
from metrics import lacking_name
import matplotlib.pyplot as plt
from datetime import datetime
from scipy import ndimage
import pandas as pd
import numpy as np
import sys

tbefore = 20.
tafter = 100.
tduration = 50.
rate = 10000
dt = 1000./rate
time_window_adjust = 50.

def fra_1(sample: pd.DataFrame,
          metric: callable,
          show: bool = True):
    """
    1. 3x3 median filter
    2. binarize above mean
    3. find peak
    """
    matrix, _, _, spls, freq = get_recording_activity(sample, metric = metric)
    filtered_matrix = ndimage.median_filter(matrix, size = 3, mode='reflect')
    binarized_filtered_matrix = np.where(filtered_matrix > np.mean(filtered_matrix), 1, 0)

    activity_mask = binarized_filtered_matrix
    no_activity_mask = (binarized_filtered_matrix - 1) ** 2
    d_prime = (np.mean(activity_mask * matrix) - np.mean(no_activity_mask * matrix)) / np.std(matrix)

    level_threshold_idx = np.where(np.max(binarized_filtered_matrix, axis = 1) == 1)[-1][-1]
    best_frequency_idx = np.where(binarized_filtered_matrix[level_threshold_idx, :] == 1)[-1]
    level_threshold = spls[level_threshold_idx]
    best_frequency = freq[best_frequency_idx]

    if show:
        binarized_filtered_matrix[level_threshold_idx, best_frequency_idx] = 2
        plt.figure()
        plt.suptitle(f"best frequency {np.round(best_frequency/1000,2)}kHz, level threshold {level_threshold}dB")
        plt.subplot(1,3,1)
        plt.title("Activity matrix")
        plt.imshow(matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,2)
        plt.title("3x3 median filtered matrix")
        plt.imshow(filtered_matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,3)
        plt.title("Boundary matrix (binarized above mean)")
        plt.imshow(binarized_filtered_matrix, cmap='inferno', aspect='auto')
        plt.show()

    return d_prime, None, best_frequency, level_threshold

def fra_2(sample: pd.DataFrame,
          show: bool = True):
    """
    1. 3x3 median filter
    2. project to obtain activity by frequency and level
    3. split the activity by frequency segment into as much parts as levels
    4. assign to each frequency the level to the part in which the activity by frequency belongs in the segment
            problem, this method assigns to all frequencies at least the maximum level, i.e. all frequencies responded at the maximum level
    5. find peak
    """
    matrix, _, _, spls, freq = get_recording_activity(sample, metric = lacking_name)
    filtered_matrix = ndimage.median_filter(matrix, size = 3, mode='reflect')
    activity_frequency = np.sum(filtered_matrix, axis = 0)
    activity_level = np.sum(filtered_matrix, axis = 1)
    step = (max(activity_frequency) - min(activity_frequency)) / len(activity_level)

    boundary_matrix = np.zeros_like(matrix)
    for freq_idx, freq_act in enumerate(activity_frequency):
        for level_idx, level_act in enumerate(activity_level):
            if level_idx * step <= freq_act - min(activity_frequency) <= (level_idx + 1) * step:
                boundary_matrix[level_idx:, freq_idx] = 0
                boundary_matrix[:level_idx, freq_idx] = 1
    level_threshold_idx = np.where(np.max(boundary_matrix, axis = 1) == 1)[-1][-1]
    best_frequency_idx = np.where(boundary_matrix[level_threshold_idx, :] == 1)[-1]
    level_threshold = spls[level_threshold_idx]
    best_frequency = freq[best_frequency_idx]


    activity_mask = boundary_matrix
    no_activity_mask = (boundary_matrix - 1) ** 2
    d_prime = (np.mean(activity_mask * matrix) - np.mean(no_activity_mask * matrix)) / np.std(matrix)

    if show:
        boundary_matrix[level_threshold_idx, best_frequency_idx] = 2
        plt.figure()
        plt.suptitle(f"best frequency {np.round(best_frequency/1000,2)}kHz, level threshold {level_threshold}dB")
        plt.subplot(1,3,1)
        plt.title("Activity matrix")
        plt.imshow(matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,2)
        plt.title("3x3 median filtered matrix")
        plt.imshow(filtered_matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,3)
        plt.title("Boundary matrix (splits of activity by freq segment)")
        plt.imshow(boundary_matrix, cmap='inferno', aspect='auto')
        plt.show()

    return d_prime, None, best_frequency, level_threshold


def fra_3(sample: pd.DataFrame,
          show: bool = True):
    """
    1. 3x3 median filter
    2. project to obtain activity by frequency
    3. best frequency is argmax
    4. take the best frequency column and define threshold as highest point in curvature
        computed using Taylor expansions, might crash due to size!
    """
    matrix, _, _, spls, freq = get_recording_activity(sample, metric = lacking_name)
    filtered_matrix = ndimage.median_filter(matrix, size = 3, mode='reflect')
    activity_frequency = np.sum(filtered_matrix, axis = 0)
    activity_level = np.sum(filtered_matrix, axis = 1)
    step = (max(activity_frequency) - min(activity_frequency)) / len(activity_level)
    best_frequency_idx = np.argmax(activity_frequency)
    best_frequency_activity = matrix[:, best_frequency_idx]
    best_frequency = freq[best_frequency_idx]

    max_sod = -1
    level_threshold_idx = 0
    for level_idx, level in enumerate(spls):
        if level_idx == 0: # using taylor's approximation!! might fail due to size
            sod = np.abs(2 * best_frequency_activity[0] - 5 * best_frequency_activity[1] + 4 * best_frequency_activity[2] - best_frequency_activity[3])
        elif level_idx == len(spls) - 1:
            sod = np.abs(2 * best_frequency_activity[-1] - 5 * best_frequency_activity[-2] + 4 * best_frequency_activity[-3] - best_frequency_activity[-4])
        else:
            sod = np.abs(best_frequency_activity[level_idx + 1] + best_frequency_activity[level_idx - 1] - 2 * best_frequency_activity[level_idx])            
        if sod > max_sod:
            max_sod = sod
            level_threshold_idx = level_idx
    level_threshold = spls[level_threshold_idx]

    if show:
        plt.figure()
        plt.suptitle(f"best frequency {np.round(best_frequency/1000,2)}kHz, level threshold {level_threshold}dB")
        plt.subplot(1,3,1)
        plt.title("Activity matrix")
        plt.imshow(matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,2)
        plt.title("3x3 median filter matrix")
        plt.imshow(filtered_matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,3)
        plt.title("Activity by level of the best frequency")
        plt.plot(spls, best_frequency_activity)
        plt.axvline(level_threshold, color='red', linestyle=':', label='Threshold (Taylor Max Curvature)')
        plt.legend()
        plt.xlabel("SPLs")
        plt.ylabel("Activity")
        plt.grid()        
        plt.show()

    return None, None, best_frequency, level_threshold


def fra_4(sample: pd.DataFrame,
          show: bool = True):
    """
    1. 3x3 median filter
    2. project to obtain activity by frequency
    3. best frequency is argmax
    4. take the best frequency column and define threshold as highest point in curvature
        computed using polynomial fitting
    """
    matrix, _, _, spls, freq = get_recording_activity(sample, metric = lacking_name)
    filtered_matrix = ndimage.median_filter(matrix, size = 3, mode='reflect')
    activity_frequency = np.sum(filtered_matrix, axis = 0)
    activity_level = np.sum(filtered_matrix, axis = 1)
    step = (max(activity_frequency) - min(activity_frequency)) / len(activity_level)
    best_frequency_idx = np.argmax(activity_frequency)
    best_frequency = freq[best_frequency_idx]
    best_frequency_activity = matrix[:, best_frequency_idx]

    degree = 4
    poly_coeffs = np.polyfit(spls, best_frequency_activity, degree) # LSE
    poly_deriv2_coeffs = np.polyder(poly_coeffs, 2)
    curvature = np.polyval(poly_deriv2_coeffs, spls)
    max_curvature_index = np.argmax(curvature)
    level_threshold = spls[max_curvature_index]

    if show:
        plt.figure()
        plt.suptitle(f"best frequency {np.round(best_frequency/1000,2)}kHz, level threshold {level_threshold}dB")
        plt.subplot(1,3,1)
        plt.title("Activity matrix")
        plt.imshow(matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,2)
        plt.title("3x3 median filter matrix")
        plt.imshow(filtered_matrix, cmap='inferno', aspect='auto')
        plt.subplot(1, 3, 3)
        plt.title("Activity by level of the best frequency")
        plt.plot(spls, best_frequency_activity, label='Original')
        spl_smooth = np.linspace(min(spls) - 1, max(spls) + 1, 50)
        act_smooth = np.polyval(poly_coeffs, spl_smooth)
        second_der_act_smooth = np.polyval(poly_deriv2_coeffs, spl_smooth)
        plt.plot(spl_smooth, act_smooth, label=f"Poly Fit (degree={degree})", linestyle='--')
        plt.plot(spl_smooth, second_der_act_smooth, color='green', label=f"Second Der Poly Fit (degree={degree})", linestyle='--')
        plt.axvline(level_threshold, color='red', linestyle=':', label='Threshold (poly. Max Curvature)')
        plt.legend()
        plt.xlabel("SPLs")
        plt.ylabel("Activity")
        plt.grid()
        plt.show()

    return None, None, best_frequency, level_threshold


def fra_5(sample: pd.DataFrame,
          show: bool = True):
    """
    1. 3x3 median filter
    2. project to obtain activity by frequency
    3. best frequency is argmax
    4. project to obtain activity by level
    5. define threshold as highest point in curvature
        computed using finite differences, problem. extrems are excluded
    """
    matrix, _, _, spls, freq = get_recording_activity(sample, metric = lacking_name)
    filtered_matrix = ndimage.median_filter(matrix, size = 3, mode='reflect')
    activity_frequency = np.sum(filtered_matrix, axis = 0)
    activity_level = np.sum(filtered_matrix, axis = 1)
    best_frequency_idx = np.argmax(activity_frequency)
    best_frequency = freq[best_frequency_idx]
    level_threshold_idx = np.argmax(np.diff(np.diff(activity_level))) + 1
    level_threshold = spls[level_threshold_idx]
    if show:
        plt.figure()
        plt.suptitle(f"best frequency {np.round(best_frequency/1000,2)}kHz, level threshold {level_threshold}dB")
        plt.subplot(1,3,1)
        plt.title("Activity matrix")
        plt.imshow(matrix, cmap='inferno', aspect='auto')
        plt.subplot(1,3,2)
        plt.title("3x3 median filter matrix")
        plt.imshow(filtered_matrix, cmap='inferno', aspect='auto')
        plt.subplot(1, 3, 3)
        plt.title("Activity by level of the best frequency")
        plt.plot(spls, activity_level, label='Original')
        plt.axvline(level_threshold, color='red', linestyle=':', label='Threshold (finite diff. Max Curvature)')
        plt.legend()
        plt.xlabel("SPLs")
        plt.ylabel("Activity")
        plt.grid()
        plt.show()

    return None, None, best_frequency, level_threshold



def healthy_and_type(sample: pd.DataFrame):
    """
    
    """
    sample = sample.sort_values(by=['level', 'frequency'], ascending=[False, True])
    # sample.assign(minimum = lambda x: min(x.recording))
    # sample.assign(maximum = lambda x: max(x.recording))
    spls = sample['level'].unique()
    freq = sample['frequency'].unique()
    print(sample)
    sys.exit(1)
    return None, None


if __name__ == "__main__":

    user = sys.argv[1]

    if user == "perecornella":
        root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
    elif user == "ar65":
        root_dir = "/Users/ar65/Library/CloudStorage/GoogleDrive-ar65@nyu.edu/My Drive/ReyesLabNYU/"
    else:
        root_dir = "toy_dataset/"

    progress_path = f'metadata/{user}/progress.csv'
    progress = pd.read_csv(progress_path)
    progress['files'] = progress.apply(
        lambda row: get_filenames(row['non checked files']) + get_filenames(row['checked files']),
        axis=1
    )
    list_of_files = progress[['name', 'files']]
    del progress

    try:
        analysis_info = pd.read(f'metadata/{user}/analisys_info.csv')
    except:
        analysis_info = pd.DataFrame(columns=['date time', 'message'])
    now = datetime.now()
    analysis_info[len(analysis_info)] = {
        'date time': now,
        'message': "fra 1 with lacking name; fra 2 with lacking name; fra 4",
    }

    analysis_results_path = f'metadata/{user}/analisys_results_{now}.csv'
    for i, row in list_of_files.iterrows():
        for file in row['files']:
            for datachannel in ["di0P", "di2P"]:
                sample, error_files = read_in_data(root_dir + row['name'], [file], datachannel=datachannel, triggerchannel="di4P")
                if not error_files:
                    healthy, type = healthy_and_type(sample)
                    d_prime_1, best_frequency_1, level_threshold_1 = fra_1(sample, 1, lacking_name, show = False)
                    d_prime_2, best_frequency_2, level_threshold_2 = fra_2(sample, 1, lacking_name, show = False)
                    best_frequency_4, level_threshold_4 = fra_4(sample, show = False)
                    results = {
                        "directory": row['name'],
                        "filename": file,
                        "channel": datachannel,
                        #"healthy",
                        #"type",
                        "best frequency 1": best_frequency_1,
                        "level threshold 1": level_threshold_1,
                        "d prime 1": d_prime_1,
                        "best frequency 2": best_frequency_2,
                        "level threshold 2": level_threshold_2,
                        "d prime 2": d_prime_2,
                        "best frequency 4": best_frequency_4,
                        "level threshold 4": level_threshold_4
                    }
