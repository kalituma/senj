import numpy as np
import scipy.interpolate

from core.util import projection_geo

def init_l1r(dct, global_dims, meta_dict, output_geolocation):
    l1r = {}
    ## write lat/lon
    if output_geolocation:
        if dct is not None:  ## compute from projection info
            # print('lat/lon computed from projection info')
            lon, lat = projection_geo(dct, add_half_pixel=False)
            l1r['lon'] = lon
            lon = None
            l1r['lat'] = lat
            lat = None

        else:  ## compute from corners given in metadata
            # print('lat/lon interpolated from metadata corners')
            pcol = [0, global_dims[1], global_dims[1], 0]
            prow = [0, 0, global_dims[0], global_dims[0]]
            plon = []
            plat = []
            band_tag = list(meta_dict['BAND_INFO'].keys())[0]
            for bk in ['UL', 'UR', 'LR', 'LL']:
                k = f'{bk}LON'
                plon.append(meta_dict['BAND_INFO'][band_tag][k])
                k = f'{bk}LAT'
                plat.append(meta_dict['BAND_INFO'][band_tag][k])

            ## set up interpolator
            zlon = scipy.interpolate.interp2d(pcol, prow, plon, kind='linear')
            zlat = scipy.interpolate.interp2d(pcol, prow, plat, kind='linear')
            x = np.arange(1, 1 + global_dims[1], 1)
            y = np.arange(1, 1 + global_dims[0], 1)
            l1r['lon'] = zlon(x, y)
            l1r['lat'] = zlat(x, y)
            x = None
            y = None
            zlat = None
            zlon = None

    return l1r