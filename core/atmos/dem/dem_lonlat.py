from core import atmos
import os

def dem_lonlat(lon, lat, source='copernicus30', default='copernicus30'):


    if source not in ['srtm', 'srtm15plus', \
                              'srtmgl1', 'srtmgl3',
                              'copernicus30', 'copernicus90',
                              'COP-DEM_GLO-30-DGED__2021_1', 'COP-DEM_GLO-30-DGED__2022_1',
                              'COP-DEM_GLO-90-DGED__2021_1', 'COP-DEM_GLO-90-DGED__2022_1']:
        print('DEM {} not recognised, using {}.'.format(source, default))
        source = '{}'.format(default)

    if source.lower() == 'srtm':
        dem = atmos.dem.hgt_lonlat(lon, lat)
    if source.lower() in ['srtmgl1', 'srtmgl3']:
        dem = atmos.dem.hgt_lonlat(lon, lat, source=source)

    if source.lower() == 'srtm15plus':
        dem = atmos.dem.srtm15plus_lonlat(lon, lat)
    if source in ['copernicus30', 'copernicus90',
                          'COP-DEM_GLO-30-DGED__2021_1', 'COP-DEM_GLO-30-DGED__2022_1',
                          'COP-DEM_GLO-90-DGED__2021_1', 'COP-DEM_GLO-90-DGED__2022_1']:
        dem = atmos.dem.copernicus_dem_lonlat(lon, lat, source=source)

    return(dem)
