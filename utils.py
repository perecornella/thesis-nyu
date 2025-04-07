import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import ndimage
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from typing import Tuple, Callable, List
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
from numpy import arange, array, concatenate, insert

### OLD METRICS FILE

def lacking_name(arr: np.array, window: List) -> float:
    """
    Calculates the variance of a window of an array taking the mean of the whole array.

    Parameters:

    arr (np.array): the array
    window (List[int,int]): min and max index.

    Returns:
    The variance

    """
    mean = np.mean(arr)

    i_min = window[0]
    i_max = window[1]

    if i_min < 0 or i_max >= len(arr):
            print('Indices are out of bounds')
            sys.exit(1)

    result = 0
    for i in range(i_min, i_max):
         result += (arr[i] - mean)**2

    result /= (i_max - i_min)
        # Calculate the variance of the slice with respect to the mean of the whole array
    return result

def windowed_variance(arr: np.array, window = None):
    if window is None:
        return np.var(arr)
    else:
        i_min = window[0]
        i_max = window[1]
        slice_arr = arr[i_min:i_max+1]
        return np.var(slice_arr)

def variance(arr: np.array, window = None):
   return np.var(arr)

def width(arr: np.array, window = None):
    i_min = window[0]
    i_max = window[1]
    if i_min < 0 or i_max >= len(arr):
            print('Indices are out of bounds')
            sys.exit(1)
    return max(arr[i_min:i_max]) - min(arr[i_min:i_max])


####


tbefore = 20.
tafter = 80.
tduration = 50.
rate = 10000
dt = 1000./rate
time_window_adjust = 50.

def get_filenames(packed_list):
    if isinstance(packed_list, list):
        return []
    else:
        packed_list = packed_list.strip("[]")
        return [item.strip(" '") for item in packed_list.split(", ") if item.strip(" '")]

def read_rs_file(PathToDFile: str, PathToHFile: str, datachannel: str, triggerchannel: str) -> Tuple[dict, dict]:
    """
    Reads a full response and returns the windows of tbefore+tduration+tafter ms where
    tones were played.

    Parameters:

    PathToDFile (str): path to d.p file
    PathToHFile (str): path to h.p file
    datachannel (str): 0, 2 (voltage) 1, 3 (current)
    triggerchannel (str): 4 (tone)

    Returns:

    Two dicts, one contains the tones played and the other the responses to those tones.

    """
    data_file = pickle.load( open( PathToDFile, "rb" ), encoding="latin1" )
    header_file = pickle.load( open( PathToHFile, "rb" ), encoding="latin1" )
    nrun = 0

    while True:
        try:
            if nrun == 0:
                rawd = data_file[datachannel + '%03d' % nrun]
                rawd4 = data_file[triggerchannel + '%03d' % nrun]
            else: 
                rawd = concatenate((rawd, data_file[datachannel + '%03d' % nrun]))
                rawd4 = concatenate((rawd4, data_file[triggerchannel + '%03d' % nrun]))
            nrun += 1
        except:
            break

    error_code = 0
    rs = []
    tones = []
    freq_spls = set()
    freq = set()
    spls = set()

    if nrun == 0:
        print(f"{datetime.now()} - Warning: Error in file {PathToDFile[-14:-3]}, wrong format of labels.")
        error_code = 2 # wrong format

    if error_code == 0:
        trigger = arange(len(rawd4))[rawd4>0.5]
        if len(trigger) == 0:
            print(f"{datetime.now()} - Warning: Error in file {PathToDFile[-14:-3]} the threshold for the trigger returned an empty list of indices.")
            error_code = 3
        if error_code == 0:
            diff = trigger[1:] - trigger[:-1]
            tonestart = trigger[concatenate((array([True]),diff>300.))]
            ntones = 0
            for key in header_file:
                if key[0:5] == 'tone_':
                    ntones += 1
            if len(tonestart) != ntones:  		
                print(f"{datetime.now()} - Warning: Error in file {PathToDFile[-14:-3]}, wrong number of tones filtered ({len(tonestart)}/{ntones}).")
                error_code = 1 # wrong number of tones filtered
            if error_code == 0:
                for i, pos in enumerate(tonestart):

                    rp = rawd[int(pos-tbefore/dt):int(pos+tduration/dt+tafter/dt-time_window_adjust/dt)]
                    padding_length = (int(pos+tduration/dt+tafter/dt-time_window_adjust/dt) - int(pos-tbefore/dt)) - len(rp)
                    padding = np.zeros(padding_length, dtype=rp.dtype)

                    frq = header_file['tone_number_%03d' % i][0]
                    spl = header_file['tone_number_%03d' % i][1]
                    rs.append({
                        "toneid": f"{PathToDFile[-7:-3]}_{str(i)}",
                        "response": np.concatenate((rp, padding))
                    }) 
                    tones.append({
                        "toneid": f"{PathToDFile[-7:-3]}_{str(i)}",
                        "frequency": frq,
                        "level": spl,
                        "else": list(header_file['tone_number_%03d' % i][2:])
                    })
                    freq.add(frq)
                    spls.add(spl)
                    freq_spls.add(f"{frq},{spl}")

    if len(freq) * len(spls) != len(freq_spls):
        error_code = 4

    return rs, tones, error_code

    # if nrun == 0:
    #     print(f"{datetime.now()} - Warning: Error in file {PathToDFile[-14:-3]}, wrong datachannel or triggerchannel labels or empty pickle files.")
    #     return [], [], 2 
    
    # trigger = np.arange(len(rawd4))[rawd4 > 0.5]
    # if len(trigger) == 0:
    #     print(f"{datetime.now()} - Warning: Error in file {PathToDFile[-14:-3]}: threshold for the trigger returned an empty list of indices.")
    #     return [], [], 3

    # diff = trigger[1:] - trigger[:-1]
    # tonestart = trigger[np.concatenate(([True], diff > 300.))]

    # ntones = 0
    # for key in header_file:
    #     if key[0:5] == 'tone_':
    #         ntones += 1

    # if len(tonestart) != ntones:
    #     print(f"{datetime.now()} - Warning: Error in file {PathToDFile[-14:-3]}, wrong number of tones filtered ({len(tonestart)}/{ntones}).")
    #     return [], [], 1

    # rs = []
    # tones = []
    # for i, pos in enumerate(tonestart):
    #     tone_id = f"{PathToDFile[-7:-3]}_{i}"
        
    #     start_idx = int(pos - tbefore / dt)
    #     end_idx = int(pos + tduration / dt + tafter / dt + 1)

    #     rp = rawd4[start_idx:end_idx]
    #     padding_length = max(0, end_idx - start_idx - len(rp))  # Ensure non-negative padding
    #     padding = np.zeros(padding_length, dtype=rp.dtype)

    #     rs.append({
    #         "toneid": tone_id,
    #         "response": np.concatenate((rp, padding))
    #     })
    #     tones.append({
    #         "toneid": tone_id,
    #         "frequency": header_file[f'tone_number_{i:03d}'][0],
    #         "level": header_file[f'tone_number_{i:03d}'][1],
    #         "else": list(header_file[f'tone_number_{i:03d}'][2:])
    #     })

    #     return rs, tones, 0


def read_rs(path_to_dir: str, files: list[str],
            datachannel: str, triggerchannel: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reads the specified set of responses in a directory.

    Parameters:

    dir_location (str): directory to read
    rec (list[int]): first file, number of files ahead
    datachannel (str): 0, 2 (voltage) 1, 3 (current)
    triggerchannel (str): 4 (tone)

    Returns: 

    Two dataframes, columns are the files and they match. One contains
    the tones the responses, the other the tonedata. 
    
    """

    batch_of_rs = []
    batch_of_tones = []
    error_rs = []
    
    for file in files:
        NameOfDFile = f"{file}d.p"
        NameOfHFile = f"{file}h.p"
        
        rs, tones, error_code = read_rs_file(path_to_dir + NameOfDFile,
                                              path_to_dir + NameOfHFile,
                                              datachannel, triggerchannel)
        batch_of_rs += rs
        batch_of_tones += tones
        
        if error_code != 0:
            error_rs.append(f"{file}:{error_code}")
    

    rs_df = pd.DataFrame(batch_of_rs, columns=["toneid", "response"])
    tones_df = pd.DataFrame(batch_of_tones, columns=["toneid", "frequency", "level", "else"])
    df = pd.merge(rs_df, tones_df, how="left", on="toneid")
    df = df[['toneid', 'response', 'frequency', 'level']]

    return df, error_rs

def fra(activity_matrix: np.array,
        mode = None):
    """
    """
    if mode == None:
        filtered_matrix = ndimage.median_filter(activity_matrix, size = 3, mode='reflect')
        activity_frequency = np.sum(filtered_matrix, axis = 0)
        activity_level = np.sum(filtered_matrix, axis = 1)

        step = (max(activity_frequency) - min(activity_frequency)) / activity_matrix.shape[0]
        best_frequency_index = np.argmax(activity_frequency)

        # Get the threshold as the maximum point of curvature
        activity_level = np.flip(activity_level)
        # sod_activity_level = activity_level[0:-2] - 2 * activity_level[1:-1] + activity_level[2:]
        # if max(sod_activity_level) < 1: # to accept min dB this value has to be tested
        #     maximum_curvature_level = 0
        # else:
        #     maximum_curvature_level = np.argmax(sod_activity_level) + 1
        # level_threshold_index = -(1 + maximum_curvature_level)

        # boundary = np.zeros(matrix.shape[1])
        # for n, activity in enumerate(activity_frequency):
        #     for i in range(matrix.shape[0]):
        #         if i * step <= activity - min(activity_frequency) <= (i + 1) * step:
        #             if i - maximum_curvature_level < 0:
        #                 boundary[n] = -1
        #             else:
        #                 boundary[n] = i - maximum_curvature_level
        #             break

        # # Calculate d'
        # tone_driven_activity = []
        # tone_unrelated_activity = [] 
        # for i, spl in enumerate(boundary): # each i i.e freq is a column in the matrix
        #     column = matrix[:, i] # get the column
        #     if spl == 1e9:
        #         tone_unrelated_activity.extend(column)
        #     else:
        #         index = np.where(spls == spl)[0][0] # the tone_driven goes from 0 to spl
        #         tone_driven_activity.extend(column[0:index+1])
        #         tone_unrelated_activity.extend(column[index+1:])
        # d_prime = (np.mean(tone_driven_activity) - np.mean(tone_unrelated_activity)) / np.std(matrix)

        return activity_frequency, activity_level

def get_rs_activity(rs: pd.DataFrame,
                           metric: callable = lacking_name):
    """
    """

    rs = rs.sort_values(by=['level', 'frequency'], ascending=[False, True])
    spls = rs['level'].unique()
    freq = rs['frequency'].unique()
    n_spls = len(spls)
    n_freq = len(freq)

    rs['activity'] = rs['response'].apply(
        lambda x: metric(arr = x, window = [int(tbefore/dt), int(tbefore/dt + tduration/dt)])
    )

    activity_matrix = np.empty((len(spls), len(freq)), dtype=float)
    print(activity_matrix.shape)
    for i, (index, row) in enumerate(rs.iterrows()):
        activity_matrix[i // n_freq, i % n_freq] = row['activity']

    activity_frequency, activity_level = fra(activity_matrix)

    return activity_matrix, \
           activity_frequency, \
           activity_level, \
           spls, \
           freq

def fra_dashboard(matrix: np.array,
                  filename: str,
                  activity_frequency : list[float],
                  activity_level : list[float],
                  spls: list[str],
                  freq: list[str],
                  boundary = None,
                  fra_summary = None): 

    fig = plt.figure(figsize=(18, 9))
    outer_grid = gridspec.GridSpec(1, 2, width_ratios=[3,2])
        
    # FRA plot
    ax1 = fig.add_subplot(outer_grid[0])
    im = ax1.imshow(matrix, cmap='inferno', aspect='auto')
    cbar = fig.colorbar(im, ax=ax1, orientation='vertical')
    cbar.set_label('Activity Level')
    ax1.set_title("FRA")
    ax1.set_xlabel("Frequency (kHz)")
    ax1.set_ylabel("SPL (dB)")
    ax1.set_xticks(np.arange(len(freq)))
    ax1.set_xticklabels(np.round(np.array(freq) / 1000, 1), rotation=45, fontsize=8)
    ax1.set_yticks(np.arange(len(spls)))
    ax1.set_yticklabels(spls, fontsize=8)

    if boundary is not None:
        for i in range(len(boundary) - 1):
            x_start, x_end = i - 0.5, i + 0.5

            if boundary[i] == 1e9:
                y_start = - 0.5
            else:
                y_start = np.where(spls == boundary[i])[0][0] + 0.5
            if boundary[i + 1] == 1e9:
                y_end = -0.5
            else:
                y_end = np.where(spls == boundary[i + 1])[0][0] + 0.5

            if boundary[i] != boundary[i + 1]:
                vertical_line = mlines.Line2D([x_end, x_end], [y_start, y_end], color="white", linewidth=3)
                ax1.add_line(vertical_line)

            horizontal_line = mlines.Line2D([x_start, x_end], [y_start, y_start], color="white", linewidth=3)
            ax1.add_line(horizontal_line)

        if boundary[-1] == 1e9:
            y_start = - 0.5
        else:
            y_start = np.where(spls == boundary[-1])[0][0] + 0.5

    inner_grid = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=outer_grid[1], hspace=0.6, wspace=0.3)

    ax0 = fig.add_subplot(inner_grid[0, 0])
    ax0.plot(
        np.arange(0, len(activity_frequency)),
        activity_frequency,
        color='dodgerblue',
        linestyle='-',
        linewidth=1,
        alpha=0.7
    )
    ax0.scatter(
        np.arange(0, len(activity_frequency)),
        activity_frequency,
        color='dodgerblue',
        edgecolor='black',
        s=25,
        alpha=0.8
    )
    ax0.set_xticks(np.arange(0, len(freq)))
    ax0.set_xticklabels(np.round(np.array(freq) / 1000, 1), rotation=45, fontsize=8)
    ax0.tick_params(axis='y', labelsize=8)
    ax0.set_title("Activity by Frequency")
    ax0.set_xlabel("Frequency (kHz)")
    ax0.set_ylabel("Activity Level")
    ax0.grid(visible=True, zorder=0, linestyle='--', alpha=0.5)

    ax1 = fig.add_subplot(inner_grid[1, 0])
    ax1.plot(
        np.arange(0, len(activity_level)),
        activity_level,
        color='tomato',
        linestyle='-',
        linewidth=1,
        alpha=0.7
    )
    ax1.scatter(
        np.arange(0, len(activity_level)),
        activity_level,
        color='tomato',
        edgecolor='black',
        s=25,
        alpha=0.8
    )
    ax1.set_xticks(np.arange(0, len(activity_level)))
    ax1.set_xticklabels(np.round(np.flip(spls), 0), rotation=45, fontsize=8)
    ax1.tick_params(axis='y', labelsize=8)
    ax1.set_title("Activity by SPL")
    ax1.set_xlabel("SPL (dB)")
    ax1.set_ylabel("Activity Level")
    ax1.grid(visible=True, zorder=0, linestyle='--', alpha=0.5)

    # Adjust spacing between main plots
    fig.suptitle(filename, fontsize=14, ha='center', y=0.95)
    fig.subplots_adjust(wspace=0.3, hspace=0.3, top=0.85, bottom=0.2)
 
    return fig

def plot_traces(rs: pd.DataFrame,
                selected_freq: list[int],
                filename: str):
    """
    """

    time_range = arange(-tbefore,tduration+tafter-time_window_adjust,dt)
    rs = rs.sort_values(by=['level', 'frequency'], ascending=[False, True])
    freq = rs['frequency'].unique()
    rs = rs[rs['frequency'].isin(freq[selected_freq])]
    spls = rs['level'].unique()
    freq = rs['frequency'].unique()
    
    # Get the range of the activity y-axis. 
    maximum = -100.
    minimum = +100.
    for arr in rs['response']:
        if maximum < max(arr):
            maximum = max(arr)
        if minimum > min(arr):
            minimum = min(arr)

    min_spl = min(rs['level'])
    min_frq = min(rs['frequency'])

    fig = plt.figure(figsize=(16,8))  

    for i, (index, row) in enumerate(rs.iterrows()):
        ax = plt.subplot(len(spls), len(freq), i + 1)
        ax.plot(time_range, row['response'][range(len(time_range))] / 1.0)

        # Set x-axis and y-axis limits, and ticks
        ax.set_ylim(minimum, maximum)
        ax.set_xlim(time_range[0], time_range[-1])
        ax.set_xticks(range(int(time_range[0]), int(time_range[-1]), 20))
        ax.tick_params(axis='x', labelsize=6, pad=10)
        ax.tick_params(axis='y', pad=10)

        # Add vertical lines at stimulus
        ax.axvline(x=0, ls='--', color='0.4', linewidth=0.8)
        ax.axvline(x=tduration, ls='--', color='0.4', linewidth=0.8)

        # Show y-axis label and add y-axis line only if this is the leftmost column
        if row["frequency"] == min_frq:
            ax.set_ylabel(f'{int(round(row["level"], 0))} dB \n voltage (mV)')
        else:
            ax.get_yaxis().set_visible(False)

        # Show x-axis label and add x-axis line only if this is the bottom row
        if row["level"] == min_spl:
            ax.set_xlabel(f'time (ms) \n{int(round(row["frequency"], 0))} Hz')
        else:
            ax.get_xaxis().set_visible(False)

        # Remove all box borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.5, hspace=0.5)
    fig.suptitle(filename, ha='center', va='top', fontsize=12, y=0.98)
    fig.tight_layout(rect=[0, 0.05, 1, 1])  

    return fig