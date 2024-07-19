from scipy.ndimage import distance_transform_edt
import numpy as np

def fillnan(data, max_distance=None):

    ## fill nans with closest value
    dis, ind = distance_transform_edt(np.isnan(data), return_distances=True, return_indices=True)
    data_filled = data[tuple(ind)]

    ## fill again with nan if greater than max_distance
    if (max_distance is not None):
        if max_distance > 0:
            sub = np.where(dis > max_distance)
            data_filled[sub] = np.nan

    return(data_filled)
