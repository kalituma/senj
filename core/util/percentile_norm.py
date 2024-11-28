import numpy as np
from sklearn.preprocessing import MinMaxScaler
from matplotlib.colors import Normalize

def percentile_norm(img:np.ndarray, p_low:float=2, p_high:float=98):

    low, high = np.nanpercentile(img, (p_low, p_high))
    pnorm = Normalize(vmin=low, vmax=high, clip=True)
    return pnorm(img)

def minmax_norm(img:np.ndarray):
    min_val = np.nanmin(img)
    max_val = np.nanmax(img)
    assert min_val < max_val, "min value should be less than max value"

    img = (img - min_val) / (max_val - min_val)
    return img

def percentile_norm_mband(img:np.ndarray, p_low:float=2, p_high:float=98):
    # added from original preprocessing code

    or_shape = img.shape
    reshaped = img.reshape(-1, img.shape[2])
    min_percentile = np.nanpercentile(reshaped, p_low)
    max_percentile = np.nanpercentile(reshaped, p_high)

    scaler1 = MinMaxScaler(feature_range=(min_percentile, max_percentile))
    scaler2 = MinMaxScaler(feature_range=(1, 255))

    reshaped = scaler1.fit_transform(reshaped)
    reshaped = scaler2.fit_transform(reshaped)

    return reshaped.reshape(or_shape)

def percentile_to_uint8(img:np.ndarray, p_low:float=2, p_high:float=98):
    img = percentile_norm(img, p_low, p_high)
    img = (img * 255).astype(np.uint8)
    return img