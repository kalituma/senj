import numpy as np
import core.atmos as atmos

def get_dem_pressure(l1r:dict, l1r_band_list:list, global_attrs:dict, user_settings:dict):

    if 'lat' in l1r_band_list and 'lon' in l1r_band_list:
        dem = atmos.dem.dem_lonlat(l1r['lon'], l1r['lat'], source=user_settings['dem_source'])
    else:
        dem = atmos.dem.dem_lonlat(global_attrs['lon'], global_attrs['lon'], source=user_settings['dem_source'])

    if dem is not None:
        dem_pressure = atmos.ac.pressure_elevation(dem)

        if user_settings['dem_pressure_resolved']:
            l1r['data_mem']['pressure'] = dem_pressure
            global_attrs['pressure'] = np.nanmean(l1r['data_mem']['pressure'])
        else:
            l1r['data_mem']['pressure'] = np.nanpercentile(dem_pressure, user_settings['dem_pressure_percentile'])
            global_attrs['pressure'] = l1r['data_mem']['pressure']
        l1r_band_list.append('pressure')

        if user_settings['dem_pressure_write']:
            l1r['data_mem']['dem'] = dem.astype(np.float32)
            l1r['data_mem']['dem_pressure'] = dem_pressure
    else:
        print('Could not determine elevation from {} DEM data'.format(user_settings['dem_source']))

    dem = None
    dem_pressure = None

    return l1r, l1r_band_list, global_attrs