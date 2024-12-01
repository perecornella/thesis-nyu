from typing import List
import numpy as np
import sys


def windowed_variance(arr: np.array, window: List) -> float:
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

    try:
        slice_arr = arr[i_min:i_max+1]
        return 1 / (i_max - i_min) * np.sum(np.square(slice_arr - mean))
    except:
        print('Indices are out of bounds')
        sys.exit(1)

def variance(arr: np.array, window = None):
    if window is None:
        return np.var(arr)
    else:
        i_min = window[0]
        i_max = window[1]
        slice_arr = arr[i_min:i_max+1]
        return np.var(slice_arr)
    
