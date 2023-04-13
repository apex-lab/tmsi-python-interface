import numpy as np

trigger_bits = 0b00000000000000001111111111111110 #bits which contain actual trigger data

def robust_reverse(x):
    """Robust function to revert a list or a numpy array given as input

    :param x: a list or a numpy array containing the signal to reverse.
    :type x: list or numpy array
    :return: list or numpy array reverted. if the wrong datatype is provided, the original input is returned.
    :rtype: list or numpy array
    """
    
    
    try:
        if isinstance(x, np.ndarray):
            return np.array([(~int(i) & trigger_bits)/2 for i in x])
        if isinstance(x, list):
            return [(~int(i) & trigger_bits)/2 for i in x]
    except:
        return x

class MaskType():
    """
    This class contains all the allowed masks.
    """
    DEFAULT = lambda x: x
    REVERSE = lambda x: [(~int(i) & trigger_bits)/2 for i in x] if isinstance(x, np.ndarray) else x
    ROBUST_REVERSE = robust_reverse