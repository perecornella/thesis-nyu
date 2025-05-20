import sys
import pickle
import numpy as np
import pandas as pd
from scipy import ndimage
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
from typing import Tuple, Callable, List
from matplotlib.backends.backend_pdf import PdfPages
from numpy import arange, array, concatenate, insert

sf_font = fm.FontProperties(fname="./config/Fonts/SFCompactRounded.ttf")

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

def read_rs_file(PathToDFile: str, PathToHFile: str, datachannel: str, triggerchannel: str) -> Tuple[dict, dict, int]:
    """
    Parses a pair of electrophysiological data files (`d.p` and `h.p`) and extracts stimulus-triggered responses.

    This function identifies the time windows in the recording where tones were played, then extracts the
    corresponding electrophysiological responses around each tone. It returns two lists of dictionaries:
    one containing the recorded responses and another containing the metadata for each tone played.

    Parameters
    ----------
    PathToDFile : str
        Full path to the binary `d.p` data file containing time-series data for multiple runs.
    
    PathToHFile : str
        Full path to the binary `h.p` header file containing tone metadata for each run.
    
    datachannel : str
        String label for the electrophysiological recording channel (e.g., 'di0P', 'di2P' for voltage, 
        'di1P', 'di3P' for current).
    
    triggerchannel : str
        String label for the trigger channel used to mark tone onset (e.g., 'di4P').

    Returns
    -------
    rs : list of dict
        A list of dictionaries, each representing a stimulus-locked response window. Each dictionary contains:
            - 'toneid' : str
                A unique ID for the tone trial, e.g., "0021_5".
            - 'response' : np.ndarray
                The signal trace surrounding the tone (with optional zero padding if needed).

    tones : list of dict
        A list of dictionaries, each representing the metadata for a tone played. Each dictionary contains:
            - 'toneid' : str
                A unique ID for the tone trial.
            - 'frequency' : float
                The frequency of the tone in Hz.
            - 'level' : float
                The sound pressure level (SPL) in dB.
            - 'else' : list
                Any additional metadata from the header (e.g., duration, waveform type).

    error_code : int
        Integer code describing any errors encountered:
            - 0: No error.
            - 1: Number of detected tones does not match number of header entries.
            - 2: Data file format error (e.g., missing runs).
            - 3: No valid trigger signal detected.
            - 4: Mismatch in frequency-level combinations (inconsistent header).

    Notes
    -----
    - The function assumes global constants `tbefore`, `tduration`, `tafter`, `dt`, and `time_window_adjust`
      are defined elsewhere in the code.
    - Each run of data is accessed sequentially (`%03d` indexing), and responses are concatenated.
    - Zero padding is used when the extracted segment is shorter than the expected window.
    - Triggers are extracted by thresholding the trigger channel at 0.5 and detecting tone onsets via 
      large jumps (>300 samples apart).

    Warnings are printed to stderr if mismatch issues are detected or parsing fails.
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
        error_code = 2 

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
                error_code = 1 
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

def fra(activity_matrix: np.array):
    """
    Computes frequency and level activity profiles from a 2D activity matrix.

    This function is designed to process a frequency-response area (FRA) matrix, where each element 
    represents the neural response at a specific frequency (columns) and sound level (rows). The function 
    smooths the matrix, then computes marginal sums along frequency and level axes to assess response strength.

    Parameters
    ----------
    activity_matrix : np.array
        A 2D NumPy array where rows correspond to sound pressure levels (SPLs) and 
        columns correspond to tone frequencies. Each value encodes some measure of 
        neural activity (e.g., spike count, signal energy).

    Returns
    -------
    activity_frequency : np.array
        A 1D array representing the total activity at each frequency (summed across levels).
    
    activity_level : np.array
        A 1D array representing the total activity at each level (summed across frequencies),
        with levels ordered from high to low SPL (i.e., array is flipped).

    Notes
    -----
    - A median filter is applied with a 3x3 neighborhood to reduce noise before computing marginal sums.
    - `activity_frequency` is the column-wise sum, showing which frequencies evoked the strongest responses.
    - `activity_level` is the row-wise sum, showing how response strength varies with SPL.
    - This function includes an optional computation of the second-order difference (SOD) of the 
      level activity curve to estimate threshold level via curvature, though that index is not returned.
    - The `step`, `best_frequency_index`, and `level_threshold_index` variables are currently computed 
      but unused in the return value. They could be useful if threshold estimation is needed.
    """

    filtered_matrix = ndimage.median_filter(activity_matrix, size = 3, mode='reflect')
    activity_frequency = np.sum(filtered_matrix, axis = 0)
    activity_level = np.sum(filtered_matrix, axis = 1)

    step = (max(activity_frequency) - min(activity_frequency)) / activity_matrix.shape[0]
    best_frequency_index = np.argmax(activity_frequency)

    activity_level = np.flip(activity_level)
    sod_activity_level = activity_level[0:-2] - 2 * activity_level[1:-1] + activity_level[2:]
    if max(sod_activity_level) < 1: 
        maximum_curvature_level = 0
    else:
        maximum_curvature_level = np.argmax(sod_activity_level) + 1
    level_threshold_index = -(1 + maximum_curvature_level)

    return activity_frequency, activity_level

def get_rs_activity(rs: pd.DataFrame):
    """
    Computes the frequency-response activity matrix and summary activity profiles from trial responses.

    This function processes a DataFrame of tone-evoked responses, sorting them by level (descending) 
    and frequency (ascending), then constructs a 2D matrix of activity values where rows represent 
    sound pressure levels (SPLs) and columns represent frequencies. Activity is measured as the variance 
    of the signal response. The matrix is passed to `fra()` to obtain marginal summaries.

    Parameters
    ----------
    rs : pd.DataFrame
        A DataFrame containing individual tone responses, with the following required columns:
            - 'level': SPL of the tone (dB)
            - 'frequency': Frequency of the tone (Hz)
            - 'response': A NumPy array representing the neural response signal

    Returns
    -------
    activity_matrix : np.ndarray
        2D array of shape (num_spls, num_freqs), where each entry is the computed activity 
        (signal variance) for a given SPL-frequency combination.

    activity_frequency : np.ndarray
        1D array of total activity at each frequency (column-wise sum of the activity matrix, after smoothing).

    activity_level : np.ndarray
        1D array of total activity at each SPL (row-wise sum of the activity matrix, after smoothing).

    spls : np.ndarray
        Array of unique SPLs in descending order, corresponding to rows of the matrix.

    freq : np.ndarray
        Array of unique frequencies in ascending order, corresponding to columns of the matrix.

    Notes
    -----
    - The function assumes that each row in `rs` corresponds to a unique tone presentation.
    - Activity is quantified using the variance (`np.var`) of the signal trace.
    - The final `activity_matrix` is ordered such that SPLs go top-to-bottom from high to low, 
      and frequencies left-to-right from low to high.
    - This function is intended to prepare input for visualization via `fra_dashboard()`.
    """

    rs = rs.sort_values(by=['level', 'frequency'], ascending=[False, True])
    spls = rs['level'].unique()
    freq = rs['frequency'].unique()
    n_spls = len(spls)
    n_freq = len(freq)
    rs['activity'] = rs['response'].apply(lambda x: np.var(x))
    activity_matrix = np.empty((len(spls), len(freq)), dtype=float)
    for i, (index, row) in enumerate(rs.iterrows()):
        activity_matrix[i // n_freq, i % n_freq] = row['activity']

    activity_frequency, activity_level = fra(activity_matrix)

    return activity_matrix, \
           activity_frequency, \
           activity_level, \
           spls, \
           freq

def fra_dashboard(matrix: np.array,
                  activity_frequency: list[float],
                  activity_level: list[float],
                  spls: list[str],
                  freq: list[str],
                  boundary=None):
    """
    Generates a frequency-response area (FRA) dashboard visualization.

    This function plots a comprehensive dashboard summarizing the neural activity across tone
    frequencies and sound pressure levels (SPLs). It includes:
      1. A heatmap of the full FRA matrix.
      2. A frequency marginal plot (activity by frequency).
      3. A level marginal plot (activity by SPL).

    Optionally, it overlays boundaries (e.g., for estimated receptive fields or tone-evoked zones)
    on the heatmap.

    Parameters
    ----------
    matrix : np.array
        2D array (levels x frequencies) representing the FRA, where each value encodes 
        the neural activity (e.g., spike count or signal power) for a tone at that level and frequency.
    
    filename : str
        Title of the figure, typically representing the source file being visualized.
    
    activity_frequency : list[float]
        Precomputed marginal sums across SPLs (columns of `matrix`), representing activity at each frequency.
    
    activity_level : list[float]
        Precomputed marginal sums across frequencies (rows of `matrix`), representing activity at each SPL.
    
    spls : list[str]
        Sound pressure levels (in dB), ordered from high to low, matching the row order of `matrix`.
    
    freq : list[str]
        Frequencies (in Hz), matching the column order of `matrix`.
    
    boundary : list[float] or None, optional
        A list of SPL values indicating the estimated boundaries of a response region per frequency bin.
        If specified, white boundary lines will be overlaid on the FRA heatmap.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The constructed matplotlib figure with subplots showing the FRA and summary plots.

    Notes
    -----
    - The heatmap uses the 'inferno' colormap for perceptual contrast.
    - The SPL plot (activity_level) flips the Y-axis order to match descending dB levels.
    - The boundary overlay draws vertical lines between regions with different thresholds.
    - This dashboard is designed for integration in electrophysiology analysis pipelines.
    """

    fig = plt.figure(figsize=(18, 9))
    outer_grid = gridspec.GridSpec(1, 2, width_ratios=[3,2])
        
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
    fig.subplots_adjust(wspace=0.3, hspace=0.3, top=0.85, bottom=0.2)
 
    return fig

def plot_traces(rs: pd.DataFrame,
                selected_freq: list[int],
                datachannel: str):
    """
    Plots time-aligned electrophysiological responses across SPLs and selected frequencies.

    This function creates a grid of subplots where each subplot corresponds to a specific 
    frequency-SPL condition. The time series traces are aligned to stimulus onset (0 ms) 
    and tone offset (`tduration`), with vertical dashed lines marking both time points.
    The y-axis units depend on the recording channel (voltage, current, or trigger signal).

    Parameters
    ----------
    rs : pd.DataFrame
        A DataFrame of responses, with required columns:
            - 'frequency': Tone frequency in Hz.
            - 'level': Sound pressure level in dB SPL.
            - 'response': NumPy array of the signal trace.

    selected_freq : list[int]
        Indices (not frequency values) indicating which frequencies to include from the 
        unique frequencies present in `rs['frequency']`.

    datachannel : str
        The name of the recording channel used. This determines the units for y-axis labeling:
            - 'di0P', 'di2P': Voltage in millivolts (mV)
            - 'di1P', 'di3P': Current in nanoamperes (nA)
            - Other (e.g., 'di4P'): Trigger signal (unitless)

    Returns
    -------
    fig : matplotlib.figure.Figure
        A matplotlib figure containing the grid of traces, sorted by SPL (rows) and frequency (columns).

    Notes
    -----
    - Global constants used: `tbefore`, `tduration`, `tafter`, `time_window_adjust`, `dt`, `sf_font`.
    - The subplot grid is arranged with SPLs from top to bottom (high to low) and frequencies left to right.
    - Response traces are normalized by 1.0 (no scaling).
    - Vertical dashed lines mark tone onset (0 ms) and offset (`tduration`).
    - Subplot spacing and labels are optimized for compact and clear layout.
    """

    colors = ['#4B1162', '#236AC6', '#261B7A']
    time_range = arange(-tbefore,tduration+tafter-time_window_adjust,dt)
    rs = rs.sort_values(by=['level', 'frequency'], ascending=[False, True])
    freq = rs['frequency'].unique()
    rs = rs[rs['frequency'].isin(freq[selected_freq])]
    spls = rs['level'].unique()
    freq = rs['frequency'].unique()
    
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
        ax.plot(time_range, row['response'][range(len(time_range))] / 1.0, color=colors[0], linewidth=0.8)

        ax.set_ylim(minimum, maximum)
        ax.set_xlim(time_range[0], time_range[-1])
        ax.set_xticks(range(int(time_range[0]), int(time_range[-1]), 20))
        for label in ax.get_xticklabels():
            label.set_fontproperties(sf_font)
            label.set_fontsize(6)

        for label in ax.get_yticklabels():
            label.set_fontproperties(sf_font)
            label.set_fontsize(6 )

        ax.axvline(x=0, ls='--', color='0.4', linewidth=0.8)
        ax.axvline(x=tduration, ls='--', color='0.4', linewidth=0.8)

        if row["frequency"] == min_frq:
            if datachannel in ['di0P', 'di2P']:
                ax.set_ylabel(f'{int(round(row["level"], 0))} dB \n voltage (mV)', fontsize=8, fontproperties=sf_font)
            elif datachannel in ['di1P', 'di3P']:
                ax.set_ylabel(f'{int(round(row["level"], 0))} dB \n current (nA)', fontsize=8, fontproperties=sf_font)
            else:
                ax.set_ylabel(f'{int(round(row["level"], 0))} dB \n trigger', fontsize=8, fontproperties=sf_font)

        else:
            ax.get_yaxis().set_visible(False)

        if row["level"] == min_spl:
            ax.set_xlabel(f'time (ms) \n{int(round(row["frequency"], 0))} Hz', fontsize=8, fontproperties=sf_font)
        else:
            ax.get_xaxis().set_visible(False)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.5, hspace=0.5)
    fig.tight_layout(rect=[0, 0.05, 1, 1])  

    return fig