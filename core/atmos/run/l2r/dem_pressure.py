import numpy as np

from core.atmos.dem import dem_lonlat
from core.atmos.ac import pressure_elevation

def get_dem_pressure(l1r:dict, l1r_band_list:list, global_attrs:dict, user_settings:dict):

    def _load_params():
        dem_source = user_settings['dem_source']
        pressure_resolved = user_settings['dem_pressure_resolved']
        pressure_percentile = user_settings['dem_pressure_percentile']
        pressure_write = user_settings['dem_pressure_write']

        return dem_source, pressure_resolved, pressure_percentile, pressure_write

    dem_source, pressure_resolved, pressure_percentile, pressure_write = _load_params()


    if 'lat' in l1r_band_list and 'lon' in l1r_band_list:
        dem = dem_lonlat(l1r['lon'], l1r['lat'], source=dem_source)
    else:
        dem = dem_lonlat(global_attrs['lon'], global_attrs['lon'], source=dem_source)

    if dem is not None:
        dem_pressure = pressure_elevation(dem)

        if pressure_resolved:
            l1r['data_mem']['pressure'] = dem_pressure
            global_attrs['pressure'] = np.nanmean(l1r['data_mem']['pressure'])
        else:
            l1r['data_mem']['pressure'] = np.nanpercentile(dem_pressure, pressure_percentile)
            global_attrs['pressure'] = l1r['data_mem']['pressure']
        l1r_band_list.append('pressure')

        if pressure_write:
            l1r['data_mem']['dem'] = dem.astype(np.float32)
            l1r['data_mem']['dem_pressure'] = dem_pressure
    else:
        print(f'Could not determine elevation from {dem_source} DEM data')

    dem = None
    dem_pressure = None

    return l1r, l1r_band_list, global_attrs