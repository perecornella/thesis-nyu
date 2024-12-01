from numpy import arange, array, concatenate, insert
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cv2 as cv
import pickle
import sys

from typing import Tuple


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
        print ('Wrong numer of tones got filtered out of the dataset.')	
        sys.exit(1)

    in_data = {}
    tonedata = {}

    for j in arange(len(tonestart)) :
        in_data[j] = rawd0[int(tonestart[j]-tbefore/dt):int(tonestart[j]+tduration/dt + tafter/dt+1)]
        tonedata[j] = list(insert(header['tone_number_%03d' % j],0,j))

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
    batch_data = {}
    batch_tonedata = {}

    for i in arange(rec[0],rec[0]+rec[1]):
        NameOfDFile = i_to_name(i, "d")
        NameOfHFile = i_to_name(i, "h")
        try:
            data, tonedata = read_in_file(path_to_dir + NameOfDFile,
                                          path_to_dir + NameOfHFile,
                                          datachannel, triggerchannel)
        except:
            print('Could not find ', NameOfDFile, ' in ' + path_to_dir + ', exit.')
            sys.exit(1)

        batch_data[NameOfDFile] = data
        batch_tonedata[NameOfHFile] = tonedata
    
    return pd.DataFrame(batch_data), pd.DataFrame(batch_tonedata)


def get_fig_size(tonedata: pd.DataFrame):
    """
    To deprecate 
    """
    return (40,20)

def activity(filename: str, data: pd.DataFrame, tonedata: pd.DataFrame,
             metric,
             title = None, show = False, sort = False):
    """
    Calculates the activity matrix of a recording. Each cell is the neural activity
    in response to a tone of a specified sound pressure level and frequency.

    Parameters:

    filename (str): 
    data (pd.DataFrame): the responses to the tones
    tonedata (pd.DataFrame): the tones spl and frequency
    show (bool): if true displays the matrix
    title (str): name to save the figures
    sort (bool): to deprecate

    Returns 
    
    """
    
    NameOfDFile = i_to_name(filename, "d")
    NameOfHFile = i_to_name(filename, "h")
   
    try:
        tonedata = pd.DataFrame(tonedata[NameOfHFile].to_list(), columns=['Index','Frequency','Intensity','tbc'])
    except:
        tonedata = pd.DataFrame(tonedata[NameOfHFile].to_list(), columns=['Index','Frequency','Intensity','tbc', 'Rise Time'])

    tonedata = tonedata.sort_values(by=['Intensity', 'Frequency'], ascending=[False, True])
    data = data[NameOfDFile]

    spls = tonedata['Intensity'].unique()
    freq = tonedata['Frequency'].unique()

    n_freq = len(freq)
    n_spls = len(spls)

    am = np.empty((len(spls), len(freq)), dtype=float)
    am_dict = []
    for i, (index, row) in enumerate(tonedata.iterrows()):

        A = metric(arr = data[row['Index']],
                   window = [int(tbefore), int(tbefore + tduration)] )
        
        am[i // n_freq, i % n_freq] = A
        am_dict.append({'Activity': A,
                        'Intensity': row['Intensity'],
                        'Frequency': row['Frequency']})

    if show:
        plt.figure(figsize=(12, 6))
        plt.imshow(am, cmap='viridis', aspect='auto') 
        plt.colorbar(label='Variance')  
        plt.title("Variance " + title)
        plt.xlabel("Frequency kHz")
        plt.ylabel("SPL dB")
        plt.xticks(ticks=np.arange(len(freq)), labels=np.round(freq/1000,1))
        plt.yticks(ticks=np.arange(len(spls)), labels=spls)
        plt.savefig('outputs/' + title + "_mv.pdf")
    
    return pd.DataFrame(am_dict, columns=['Activity', 'Intensity', 'Frequency'])


    # seg_am = np.zeros((len(spls), len(freq)), dtype=float)
    # seg_am[am > 0.9 * np.mean(am)] = 1 # Binary segmentation

    # kernel = np.ones((2,1),np.uint8)
    # seg_am_open = cv.morphologyEx(seg_am, cv.MORPH_OPEN, kernel, borderValue = 0)
    # show = False
    # if sum(sum(seg_am_open)) > 2 * n_spls:
    #     show = True
    # seg_am[seg_am_open == 1] = 2

    # target = [n_spls - 1, 2]
    # if sort:
    #     show = False
    #     for i in range(n_spls - (target[0] - 1)):
    #         for j in range(n_freq - (target[1] - 1)):

    #             if np.array_equal(seg_am[i:i+target[0], j:j+target[1]], np.ones((target[0], target[1]), dtype=int)):
    #                 seg_am[i:i+target[0], j:j+target[1]] = 2    
    #                 show = True
    #                 break

    # plt.figure(figsize=(12, 6))
    # plt.imshow(seg_am, cmap='viridis', aspect='auto') 
    # plt.colorbar(label='Class')  
    # plt.title("Segmented Variance" + title)
    # plt.xlabel("Frequency kHz")
    # plt.ylabel("SPL dB")
    # plt.xticks(ticks=np.arange(len(freq)), labels=np.round(freq/1000,1))
    # plt.yticks(ticks=np.arange(len(spls)), labels=spls)
    # plt.savefig('outputs/' + title + "_mv_bin.pdf")


def raw_data_plot(file: int, data: pd.DataFrame, tonedata: pd.DataFrame, title: str):
    """
    Plot the traces of activity for an experiment.

    Parameters

    file (int): Number of file in the directory of experiments.
    data (pd.DataFrame): the responses to the tones
    tonedata (pd.DataFrame): the tones spl and frequency
    title (str): name to save the figures
    """

    NameOfDFile = i_to_name(file, "d")
    NameOfHFile = i_to_name(file, "h")
   
    rise_time = False
    try:
        tonedata = pd.DataFrame(tonedata[NameOfHFile].to_list(), columns=['Index','Frequency','Intensity','tbc'])
    except:
        tonedata = pd.DataFrame(tonedata[NameOfHFile].to_list(), columns=['Index','Frequency','Intensity','tbc', 'Rise Time'])
        rise_time = True

    tonedata = tonedata.sort_values(by=['Intensity', 'Frequency'], ascending=[False, True])
    data = data[NameOfDFile]

    time = arange(-tbefore,tduration+tafter+dt,dt)
    spls = len(tonedata['Intensity'].unique())
    freq = len(tonedata['Frequency'].unique())

    # Get the range of the activity y-axis. 
    maximum = -100.
    minimum = +100.
    for arr in data:
        if maximum < max(arr):
            maximum = max(arr)
        if minimum > min(arr):
            minimum = min(arr)

    min_spl = min(tonedata['Intensity'])
    min_frq = min(tonedata['Frequency'])

    fig = plt.figure(figsize=get_fig_size(tonedata))  

    for arr in data:
        if len(arr) != len(time):
            print("error")
            sys.exit(1)

    for i, (index, row) in enumerate(tonedata.iterrows()):
        ax = plt.subplot(spls, freq, i + 1)
        ax.plot(time, data[int(row['Index'])] / 1.0)

        # Set x-axis and y-axis limits, and ticks
        ax.set_ylim(minimum, maximum)
        ax.set_xlim(time[0], time[-1])
        ax.set_xticks(range(int(time[0]), int(time[-1]), 20))
        ax.tick_params(axis='x', labelsize=6, pad=10)
        ax.tick_params(axis='y', pad=10)

        # Add vertical lines at stimulus
        ax.axvline(x=0, ls='--', color='0.4', linewidth=0.8)
        ax.axvline(x=tduration, ls='--', color='0.4', linewidth=0.8)
        if rise_time:
            ax.axvspan(0, row['Rise Time'], color=(0.6, 0.8, 1, 0.4))

        # Show y-axis label and add y-axis line only if this is the leftmost column
        if row["Frequency"] == min_frq:
            ax.set_ylabel(f'Intensity: {int(round(row["Intensity"], 0))} dB')
            ax.axvline(0, color='black', linewidth=0.5)  # y-axis line
        else:
            ax.get_yaxis().set_visible(False)

        # Show x-axis label and add x-axis line only if this is the bottom row
        if row["Intensity"] == min_spl:
            ax.set_xlabel(f'time (ms) \n{int(round(row["Frequency"], 0))} Hz')
            ax.axhline(0, color='black', linewidth=0.5)  # x-axis line
        else:
            ax.get_xaxis().set_visible(False)

        # Remove all box borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.5, hspace=0.5)
    plt.suptitle(title, ha='center', va='top', fontsize=11, y=0.98)
    plt.savefig('outputs/' + title + "_r.pdf")
    plt.close()

