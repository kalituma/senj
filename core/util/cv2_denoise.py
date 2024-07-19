import numpy as np
import cv2

def nonlocal_mean_denoising(img_arr:np.ndarray, h:float=10, templateWindowSize:int=7, searchWindowSize:int=21, norm_func=None):

    target = img_arr.copy()

    if norm_func is not None:
        target = norm_func(target)
        target *= 255
        target = img_arr.astype(np.uint8)

    result = cv2.fastNlMeansDenoising(target, None, h, templateWindowSize, searchWindowSize)

    return result