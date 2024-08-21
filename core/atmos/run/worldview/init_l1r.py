import numpy as np
import scipy.interpolate

from core.util import projection_geo

def init_l1r(dct, global_dims, meta_dict, output_geolocation):
    l1r = {}
    ## write lat/lon
    if output_geolocation:
        # print('lat/lon computed from projection info')
        lon, lat = projection_geo(dct, add_half_pixel=False)
        l1r['lon'] = lon.astype(np.float32)
        lon = None
        l1r['lat'] = lat.astype(np.float32)
        lat = None

    return l1r