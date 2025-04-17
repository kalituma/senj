from skimage import exposure
from typing import Dict
import numpy as np

def equalize_histogram(band_arr:np.ndarray) -> np.ndarray:
    return exposure.equalize_hist(band_arr)
