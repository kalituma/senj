from pyhdf.SD import SD, SDC
import numpy as np
from scipy import interpolate

from core import atmos


def interp_ozone(file, lon, lat, dataset='ozone', kind='linear'):

    ## input geolocation dimensions
    dim = np.atleast_1d(lon).shape
    onedim = (len(dim) == 1) & (dim[0] == 1)

    ## open ozone file
    f = SD(file, SDC.READ)
    datasets_dic = f.datasets()
    meta = f.attributes()
    sds_obj = f.select(dataset)
    data = sds_obj.get()
    f.end()
    f = None

    ## make lons and lats for this file
    lons = np.linspace(meta["Westernmost Longitude"], meta["Easternmost Longitude"],
                        num = meta['Number of Columns'])
    lats = np.linspace(meta["Northernmost Latitude"], meta["Southernmost Latitude"],
                        num = meta['Number of Rows'])

    ## make lons/lats 2D for reproject2
    if not onedim:
        lons = np.repeat(np.broadcast_to(lons, (1, data.shape[1])), data.shape[0], axis=0)
        lats = np.repeat(np.expand_dims(lats, axis=1), data.shape[1], axis=1)

    ## old 1D interp
    if onedim:
        ## do interpolation in space
        if kind == 'nearest':
            xi,xret = min(enumerate(lons), key=lambda x: abs(x[1]-float(lon)))
            yi,yret = min(enumerate(lats), key=lambda x: abs(x[1]-float(lat)))
            uoz = data[yi,xi]/1000.
        else:
            interp = interpolate.interp2d(lons, lats, data, kind=kind)
            uoz = (interp(lon, lat))[0]
    ## 2D interp
    else:
        uoz = atmos.shared.reproject2(data, lons, lats, lon, lat,
                                      nearest=kind == 'nearest',
                                      radius_of_influence=10e5)

    anc_ozone = {'ozone':{'interp':uoz}}
    return(anc_ozone)
