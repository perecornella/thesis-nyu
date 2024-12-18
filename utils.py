import sys
import pickle
import numpy as np
import pandas as pd
from scipy import ndimage
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from typing import Tuple, Callable
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
from metrics import lacking_name
from numpy import arange, array, concatenate, insert

tbefore = 20.
tafter = 100.
tduration = 50.
rate = 10000
dt = 1000./rate

def i_to_name(i, mode):
    if mode == "d":
        return 'A%03dd.p' % i
    elif mode == "h":
        return 'A%03dh.p' % i 

def read_in_file(PathToDFile: str, PathToHFile: str, datachannel: str, triggerchannel: str) -> Tuple[dict, dict]:
    """
    Reads a full recording and returns the windows of tbefore+tduration+tafter ms where
    tones were played.

    Parameters:

    PathToDFile (str): path to d.p file
    PathToHFile (str): path to h.p file
    datachannel (str): 0, 2 (voltage) 1, 3 (current)
    triggerchannel (str): 4 (tone)

    Returns:

    Two dicts, one contains the tones played and the other the responses to those tones.

    """

    data = pickle.load( open( PathToDFile, "rb" ), encoding="latin1" )
    header = pickle.load( open( PathToHFile, "rb" ), encoding="latin1" )

    nrun = 0 # 0..number_of_runs
    channelname = datachannel + '%03d' % nrun
    triggername = triggerchannel + '%03d' % nrun
    while True:
        if nrun == 0:
            rawd0 = data[channelname]
            rawd4 = data[triggername]
        else :
            rawd0 = concatenate((rawd0,data[channelname]))
            rawd4 = concatenate((rawd4,data[triggername]))
        nrun+=1
        channelname = datachannel + '%03d' % nrun
        triggername = triggerchannel + '%03d' % nrun
        try :
            tmp = data[channelname]
        except :
            break

    trigger = arange(len(rawd4))[rawd4>0.5]	
    diff = trigger[1:] - trigger[:-1]
    tonestart = trigger[concatenate((array([True]),diff>300.))]

    ntones = 0
    for key in header:
        if key[0:5] == 'tone_':
            ntones += 1
    
    if len(tonestart) != ntones:  		
        print ('Wrong numer of tones got filtered out of the file', PathToDFile[-7:-3])	
        sys.exit(1)

    in_data = []
    tonedata = []

    for j in arange(len(tonestart)) :
        in_data.append({
            "toneid": PathToDFile[-7:-3] + "_" + str(j),
            "recording": rawd0[int(tonestart[j]-tbefore/dt):int(tonestart[j]+tduration/dt + tafter/dt+1)]})
        
        tone = header['tone_number_%03d' % j]
        tonedata.append({
            "toneid": PathToDFile[-7:-3] + "_" + str(j),
            "frequency": tone[0],
            "level": tone[1],
            "else": list(tone[2:-1])})

    return in_data, tonedata

def read_in_data(path_to_dir: str, rec: list[int],
                 datachannel: str, triggerchannel: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reads the specified set of recordings in a directory.

    Parameters:

    dir_location (str): directory to read
    rec (list[int]): first file, number of files ahead
    datachannel (str): 0, 2 (voltage) 1, 3 (current)
    triggerchannel (str): 4 (tone)

    Returns: 

    Two dataframes, columns are the files and they match. One contains
    the tones the responses, the other the tonedata. 
    
    """
    batch_data = []
    batch_tonedata = []

    error_files = []
    for i in arange(rec[0],rec[0]+rec[1]):
        NameOfDFile = i_to_name(i, "d")
        NameOfHFile = i_to_name(i, "h")

        try:
            data, tonedata = read_in_file(path_to_dir + NameOfDFile,
                                            path_to_dir + NameOfHFile,
                                            datachannel, triggerchannel)
            batch_data += data
            batch_tonedata += tonedata
        
        except:
            print('Error in file', NameOfDFile[0:4], ' in ' + path_to_dir[-7:] + ', pass.')
            error_files.append(NameOfDFile[0:4])
            pass
    

    data_df = pd.DataFrame(batch_data, columns=["toneid", "recording"])
    tonedata_df = pd.DataFrame(batch_tonedata, columns=["toneid", "frequency", "level", "else"])

    return data_df, tonedata_df, error_files

def fra(average_activity: pd.DataFrame):
    """
    Calculates the FRA (frequency-response-area) of a recording. Each cell is the neural activity
    in response to a tone of a specified sound pressure level and frequency.

    Parameters:

    data (pd.DataFrame): TODO
    metric (function): TODO

    Returns 
    
    """

    spls = average_activity['level'].unique()
    freq = average_activity['frequency'].unique()
    n_spls = len(spls)
    n_freq = len(freq)

    matrix = np.empty((len(spls), len(freq)), dtype=float)
    for i, (index, row) in enumerate(average_activity.iterrows()):
        matrix[i // n_freq, i % n_freq] = row['activity'] # row['level'] + row['frequency'] / 1000

    filtered_matrix = ndimage.median_filter(matrix, size = 3, mode='reflect')
    activity_frequency = np.sum(filtered_matrix, axis = 0)
    activity_level = np.sum(filtered_matrix, axis = 1)
    step = (max(activity_frequency) - min(activity_frequency)) / n_spls
    best_frequency = freq[np.argmax(activity_frequency)]
    
    activity_level = np.flip(activity_level)
    sod_activity_level = activity_level[0:-2] - 2 * activity_level[1:-1] + activity_level[2:]
    if max(sod_activity_level) < 1: # to accept min dB this value has to be tested
        maximum_curvature_level = 0
    else:
        maximum_curvature_level = np.argmax(sod_activity_level) + 1
    level_threshold = spls[-(1 + maximum_curvature_level)]

    boundary = np.zeros(n_freq)
    for n, activity in enumerate(activity_frequency):
        for i in range(n_spls):
            if i * step <= activity - min(activity_frequency) <= (i + 1) * step:
                if i - maximum_curvature_level < 0:
                    boundary[n] = 1e9
                else:
                    boundary[n] = spls[i - maximum_curvature_level]
                break

    # Calculate d'
    tone_driven_activity = []
    tone_unrelated_activity = [] 
    for i, spl in enumerate(boundary): # each i i.e freq is a column in the matrix
        column = matrix[:, i] # get the column
        if spl == 1e9:
            tone_unrelated_activity.extend(column)
        else:
            index = np.where(spls == spl)[0][0] # the tone_driven goes from 0 to spl
            tone_driven_activity.extend(column[0:index+1])
            tone_unrelated_activity.extend(column[index+1:])
    d_prime = (np.mean(tone_driven_activity) - np.mean(tone_unrelated_activity)) / np.std(matrix)

    # print(boundary)
    # result = np.concatenate([
    #     np.array([0]),  # Padding at the beginning
    #     sod_activity_level,  # Second derivative
    #     np.array([0])   # Padding at the end
    # ])

    # plt.figure()
    # plt.plot(activity_level)
    # plt.plot(result, color='red')
    # plt.show()

    fra_summary = pd.DataFrame([{'d prime': d_prime, 'best frequency': best_frequency, 'level threshold': level_threshold}])
    return fra_summary, matrix, boundary

def fra_dashboard(data: pd.DataFrame,
                   filename: str): 

    fig = plt.figure(figsize=(18, 9))
    outer_grid = gridspec.GridSpec(1, 2, width_ratios=[3,2])
    
    # 

    metric = lacking_name
    df = data[['toneid', 'recording', 'frequency', 'level']]
    df['activity'] = df['recording'].apply(lambda x: metric(arr = x, window = [int(tbefore/dt), int(tbefore/dt + tduration/dt)]))
    
    average_activity = df.groupby(['frequency', 'level'])['activity'].mean().reset_index()
    average_activity = average_activity.sort_values(by=['level', 'frequency'], ascending=[False, True])
    fra_summary, matrix, boundary = fra(average_activity)

    # average_activity2 = df.groupby(['frequency', 'level'])['activity'].mean().reset_index()
    # average_activity2 = average_activity2.sort_values(by=['level', 'frequency'], ascending=[False, True])
    # fra_summary3, matrix3, boundary3 = fra(average_activity2, metric = )

    # average_activity3 = df.groupby(['frequency', 'level'])['activity'].mean().reset_index()
    # average_activity3 = average_activity3.sort_values(by=['level', 'frequency'], ascending=[False, True])
    # fra_summary3, matrix3, boundary3 = fra(average_activity3, metric = )

    df = df.sort_values(by=['level', 'frequency'], ascending=[False, True])
    spls = df['level'].unique()
    freq = df['frequency'].unique()

    # FRA plot
    ax1 = fig.add_subplot(outer_grid[0])
    ax1.imshow(matrix, cmap='inferno', aspect='auto')
    # ax1.colorbar(im, ax=ax, label='Activity')
    ax1.set_title("FRA")
    ax1.set_xlabel("Frequency (kHz)")
    ax1.set_ylabel("SPL (dB)")
    ax1.set_xticks(np.arange(len(freq)))
    ax1.set_xticklabels(np.round(freq / 1000, 1))
    ax1.set_yticks(np.arange(len(spls)))
    ax1.set_yticklabels(spls)
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

    # Best recordings plot
    inner_grid = gridspec.GridSpecFromSubplotSpec(len(spls), 1, subplot_spec=outer_grid[1], hspace=0.4, wspace=0.3)

    best_frequency = fra_summary['best frequency'].iloc[0]
    best_frequency_recordings = df[df['frequency'] == best_frequency]
    best_frequency_recordings = best_frequency_recordings.sort_values(by=['level', 'frequency'], ascending=[False, True])
    time_range = arange(-tbefore,tduration+tafter+dt,dt)

    # Get the range of the activity y-axis. 
    y_maximum = -100.
    y_minimum = +100.
    for arr in best_frequency_recordings['recording']:
        if y_maximum < max(arr):
            y_maximum = max(arr)
        if y_minimum > min(arr):
            y_minimum = min(arr)

    min_spl = min(df['level'])

    for i, (index, row) in enumerate(best_frequency_recordings.iterrows()):
        ax = fig.add_subplot(inner_grid[i, 0])
        ax.plot(time_range, row['recording'] / 1.0)

        ax.set_ylim(y_minimum, y_maximum)
        ax.set_xlim(time_range[0], time_range[-1])
        ax.set_xticks(range(int(time_range[0]), int(time_range[-1]), 20))
        ax.tick_params(axis='x', labelsize=6, pad=10)
        ax.tick_params(axis='y', pad=10)

        # Add vertical lines at stimulus
        ax.axvline(x=0, ls='--', color='0.4', linewidth=0.8)
        ax.axvline(x=tduration, ls='--', color='0.4', linewidth=0.8)
        ax.set_ylabel(f'{round(row['level'], 2)} dB')
        if row['level'] == min_spl:
            ax.set_xlabel(f'time (ms) \n{round(row['level'], 0)} Hz')
        else:
            ax.get_xaxis().set_visible(False)

        # Remove all box borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    summary_text = f"""
    d': {fra_summary['d prime'].iloc[0]:.2f}
    Best Frequency: {fra_summary['best frequency'].iloc[0] / 1000:.1f} kHz
    Level Threshold: {fra_summary['level threshold'].iloc[0]} dB
    Min voltage: {y_minimum:.1f} V
    Max voltage: {y_maximum:.1f} V    
    """
    fig.text(
        0.5, 0.06,  # Adjusted vertical position for better visibility
        summary_text.strip(),
        ha='center',
        va='center',
        fontsize=10,
    )

    # Adjust spacing between main plots
    # fig.suptitle(filename, fontsize=12, ha='center')
    fig.suptitle("Hello Alex", fontsize=12, ha='center')
    fig.subplots_adjust(wspace=0.3, hspace=0.3, top=0.92, bottom=0.2)
 

    return [round(fra_summary['d prime'].iloc[0],2),
            round(fra_summary['best frequency'].iloc[0],2),
            round(fra_summary['level threshold'].iloc[0],2)], fig

def all_traces(data: pd.DataFrame,
               filename: str):
    """
    """

    data = data.sort_values(by=['level', 'frequency'], ascending=[False, True])
    time_range = arange(-tbefore,tduration+tafter+dt,dt)
    spls = len(data['level'].unique())
    freq = len(data['frequency'].unique())

    # Get the range of the activity y-axis. 
    maximum = -100.
    minimum = +100.
    for arr in data['recording']:
        if maximum < max(arr):
            maximum = max(arr)
        if minimum > min(arr):
            minimum = min(arr)

    min_spl = min(data['level'])
    min_frq = min(data['frequency'])

    fig = plt.figure(figsize=(16,8))  

    for arr in data['recording']:
        if len(arr) != len(time_range):
            print("error")
            sys.exit(1)

    for i, (index, row) in enumerate(data.iterrows()):
        ax = plt.subplot(spls, freq, i + 1)
        ax.plot(time_range, row['recording'] / 1.0)

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
            ax.set_ylabel(f'{int(round(row["level"], 0))} dB')
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

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.5, hspace=0.5)
    plt.suptitle(filename, ha='center', va='top', fontsize=12, y=0.98)
    fig.tight_layout(rect=[0, 0.05, 1, 1])  

    return fig