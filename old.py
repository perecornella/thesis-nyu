
def recording_plot(data: pd.DataFrame):
    """
    Plot the traces of activity for an experiment.

    Parameters

        data (pd.DataFrame): the responses to the tones

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

    fig = plt.figure()  

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
            ax.axvline(0, color='black', linewidth=0.5)  # y-axis line
        else:
            ax.get_yaxis().set_visible(False)

        # Show x-axis label and add x-axis line only if this is the bottom row
        if row["level"] == min_spl:
            ax.set_xlabel(f'time (ms) \n{int(round(row["frequency"], 0))} Hz')
            ax.axhline(0, color='black', linewidth=0.5)  # x-axis line
        else:
            ax.get_xaxis().set_visible(False)

        # Remove all box borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.5, hspace=0.5)
    plt.suptitle("RAW", ha='center', va='top', fontsize=11, y=0.98)
    fig.tight_layout(rect=[0, 0.05, 1, 1])  

    return fig




def calculate_spikes(arr, number_of_sds = 2.3):
    return np.where(arr > number_of_sds * np.std(arr))


def spikes_plot(data: pd.DataFrame, tonedata: pd.DataFrame, rec: list[int], title: str):

    Mock_File = i_to_name(0, mode="h")
    rise_time = False
    try:
        tonedata = pd.DataFrame(tonedata[Mock_File].to_list(), columns=['Index','Frequency','Intensity','tbc'])
    except:
        tonedata = pd.DataFrame(tonedata[Mock_File].to_list(), columns=['Index','Frequency','Intensity','tbc', 'Rise Time'])
        rise_time = True

    tonedata = tonedata.sort_values(by=['Intensity', 'Frequency'], ascending=[False, True])

    time_range = arange(-tbefore,tduration+tafter+dt,dt)
    spls = len(tonedata['Intensity'].unique())
    freq = len(tonedata['Frequency'].unique())

    min_spl = min(tonedata['Intensity'])
    min_frq = min(tonedata['Frequency'])

    fig = plt.figure()  

    for i, (index, row) in enumerate(tonedata.iterrows()):
        ax = plt.subplot(spls, freq, i + 1)

        prob = np.zeros(len(time_range))
        for i in range(rec[0], rec[0] + rec[1]):
            spikes = calculate_spikes(data[i_to_name(i, mode="d")].iloc[int(row['Index'])])
            prob[spikes] += 1

        ax.hist(prob, bins=int(len(time_range)/30))

        # Set x-axis and y-axis limits, and ticks
        ax.set_ylim(0, 1)
        ax.set_xlim(time_range[0], time_range[-1])
        ax.set_xticks(range(int(time_range[0]), int(time_range[-1]), 20))
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
    plt.show()

def output_name(name, ext):
    current_time = time.localtime()
    formatted_date = time.strftime("%d_%m_%y", current_time)
    
    return "outputs/" + formatted_date + "_" + name + "." + ext





def plot_experiment(data: pd.DataFrame):
    """
    Plot the traces of activity for an experiment.

    Parameters

        data (pd.DataFrame): the responses to the tones

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

    fig = plt.figure()  

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
            ax.axvline(0, color='black', linewidth=0.5)  # y-axis line
        else:
            ax.get_yaxis().set_visible(False)

        # Show x-axis label and add x-axis line only if this is the bottom row
        if row["level"] == min_spl:
            ax.set_xlabel(f'time (ms) \n{int(round(row["frequency"], 0))} Hz')
            ax.axhline(0, color='black', linewidth=0.5)  # x-axis line
        else:
            ax.get_xaxis().set_visible(False)

        # Remove all box borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, wspace=0.5, hspace=0.5)
    plt.suptitle("RAW", ha='center', va='top', fontsize=11, y=0.98)
    fig.tight_layout(rect=[0, 0.05, 1, 1])  

    return fig


def calculate_spikes(arr, number_of_sds = 2.3):
    return np.where(arr > number_of_sds * np.std(arr))


def spikes_plot(data: pd.DataFrame, tonedata: pd.DataFrame, rec: list[int], title: str):

    Mock_File = i_to_name(0, mode="h")
    rise_time = False
    try:
        tonedata = pd.DataFrame(tonedata[Mock_File].to_list(), columns=['Index','Frequency','Intensity','tbc'])
    except:
        tonedata = pd.DataFrame(tonedata[Mock_File].to_list(), columns=['Index','Frequency','Intensity','tbc', 'Rise Time'])
        rise_time = True

    tonedata = tonedata.sort_values(by=['Intensity', 'Frequency'], ascending=[False, True])

    time_range = arange(-tbefore,tduration+tafter+dt,dt)
    spls = len(tonedata['Intensity'].unique())
    freq = len(tonedata['Frequency'].unique())

    min_spl = min(tonedata['Intensity'])
    min_frq = min(tonedata['Frequency'])

    fig = plt.figure()  

    for i, (index, row) in enumerate(tonedata.iterrows()):
        ax = plt.subplot(spls, freq, i + 1)

        prob = np.zeros(len(time_range))
        for i in range(rec[0], rec[0] + rec[1]):
            spikes = calculate_spikes(data[i_to_name(i, mode="d")].iloc[int(row['Index'])])
            prob[spikes] += 1

        ax.hist(prob, bins=int(len(time_range)/30))

        # Set x-axis and y-axis limits, and ticks
        ax.set_ylim(0, 1)
        ax.set_xlim(time_range[0], time_range[-1])
        ax.set_xticks(range(int(time_range[0]), int(time_range[-1]), 20))
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
    plt.show()

def output_name(name, ext):
    current_time = time.localtime()
    formatted_date = time.strftime("%d_%m_%y", current_time)
    
    return "outputs/" + formatted_date + "_" + name + "." + ext









### keeeeeep



from metrics import windowed_variance, variance, lacking_name, width
from utils import read_in_data, plot_dashboard
from widget import launch_data_entry_widget
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

## INPUT

datachannel = 'di0P'
triggerchannel = 'di4P'

# Main

# plt.ion() 

root_dir = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
dir_info = pd.read_csv('metadata/dir_info.csv')

def process_data(data):
    print("Data processed:", data)


for i, dir in dir_info.iterrows():
    for start_file in range(dir["Min file"], dir["Max file"] - dir["Min file"], 10):
        data, tonedata, error_files = read_in_data(root_dir + dir["Name"], [start_file, 10], datachannel, triggerchannel)
        df = pd.merge(data, tonedata, how="left", on="toneid")

        for file in range(start_file, start_file + 10):
            if f"A{file:03d}" not in error_files:
                sample = df[df["toneid"].str.startswith(f"A{file:03d}")]
                plot_dashboard(sample, metric=lacking_name, filename=f"{dir['Name']}A{file:03d} channel di0P")



                