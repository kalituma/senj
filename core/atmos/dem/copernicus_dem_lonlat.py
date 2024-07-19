import os
import numpy as np
from core import atmos
from core.util import read_band, projection_geo


def copernicus_dem_lonlat(lon1, lat1, sea_level=0, source='copernicus30', nearest=False, dem_min = -500.0):

    ## get limit based on lat lon and find and download DEM tiles
    limit = np.nanmin(lat1), np.nanmin(lon1), np.nanmax(lat1), np.nanmax(lon1)
    dem_tiles = atmos.dem.copernicus_dem_find(limit, source = source)

    dem = None
    ## run through dem files and reproject data to target lat,lon
    for i, dem_tile in enumerate(dem_tiles):
        if len(dem_tile) < 21: continue
        if not os.path.exists(dem_tile):
            print('{} does not exist.'.format(dem_tile))
            continue

        cdm = read_band(dem_tile)
        dct = atmos.shared.projection_read(dem_tile)
        lon0, lat0 = projection_geo(dct)

        result = atmos.shared.reproject2(cdm, lon0, lat0, lon1, lat1, nearest=nearest)
        if dem is None:
            dem = result
        else:
            dem[result > dem_min] = result[result > dem_min]
    if dem is not None: dem[dem<=dem_min] = sea_level

    return(dem)
