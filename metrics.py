from typing import List
import numpy as np
import sys


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
