import cv2
import numpy as np
import matplotlib.pyplot as plt



def rescale_images_linear(le: np.array) -> np.array:
    '''
    Helper function to rescale images in visible range
    '''
    le_min = le[le != -float('inf')].min()
    le_max = le[le != float('inf')].max()
    le[le==float('inf')] = le_max
    le[le==-float('inf')] = le_min

    le = (le - le_min) / (le_max - le_min)

    return le


def rescale_to_non_zero(le: np.array, const: float = 0.1) -> np.array:
    '''
    Helper function to rescale images to be above 0
    '''
    le_min = le.min()
    le = le - le_min + const

    return le