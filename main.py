import sys
import numpy as np
import pandas as pd
from utils import read_in_file, read_in_data, raw_data_plot, activity
from metrics import windowed_variance

## INPUT

datachannel = str(0)
starting_file = 58
number_of_files = 1
experiment = str(140412)

# Get the channel

datachannel = 'di'+datachannel+'P'
triggerchannel = 'di4P'

# Reading settings

rec = np.array([starting_file,number_of_files])
dir_location = "/Users/perecornella/Library/CloudStorage/GoogleDrive-pere.cornella@estudiantat.upc.edu/My Drive/ReyesLabNYU/"
dir_location = dir_location + experiment + "/"
data, tonedata = read_in_data(dir_location, rec, datachannel, triggerchannel)

for file in range(rec[0], rec[0] + rec[1]):
    title = experiment + "_" + 'A%03d' % file + "_" + 'ch' + datachannel[2]
    raw_data_plot(file, data, tonedata, title)
    activity(file, data, tonedata, metric = windowed_variance, title = title, show=True)


#### COLUMN TBC IN TONEDATA FILE ####
# import matplotlib.pyplot as plt
# print(tonedata)
# plt.figure()
# plt.scatter(tonedata['A114h.p'].apply(lambda x: x[2]), tonedata['A114h.p'].apply(lambda x: x[3]))
# plt.scatter(tonedata['A050h.p'].apply(lambda x: x[2]), tonedata['A050h.p'].apply(lambda x: x[3]))
# plt.show()