from typing import TYPE_CHECKING
import os, json
import numpy as np
import dateutil.parser

import core.atmos as atmos
from core.atmos.shared import projection_sub, projection_netcdf
from core.util import distance_se, rsr_read, rsr_convolute_dict, projection_read, projection_geo
from core.atmos.run.planet import init_l1r, get_l1r_band

if TYPE_CHECKING:
    from core.raster import Raster

def build_planet_l1r(target_raster: "Raster", meta_dict:dict, user_settings:dict,
                     check_sensor=True, check_time=True, max_merge_time=600,  # seconds
                     from_radiance=False, gains=False, gains_toa=None,
                     percentiles_compute=True,
                     percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    dtime = dateutil.parser.parse(meta_dict['isotime'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    limit = user_settings['limit']
    output_geolocation = user_settings['output_geolocation']
    output_geometry = user_settings['output_geometry']
    output_xy = user_settings['output_xy']
    netcdf_projection = user_settings['netcdf_projection']

    vname = user_settings['region_name']
    gains = user_settings['gains']
    gains_toa = user_settings['gains_toa']

    rsrf = atmos.config['data_dir'] + f'/RSR/{meta_dict["sensor"]}.txt'
    rsr, rsr_bands = rsr_read(rsrf)
    waves = np.arange(250, 2500) / 1000
    waves_mu = rsr_convolute_dict(waves, waves, rsr)
    waves_names = {f'{b}': f'{waves_mu[b] * 1000:.0f}' for b in waves_mu}

    f0 = atmos.shared.f0_get(f0_dataset=user_settings['solar_irradiance_reference'])
    f0_b = rsr_convolute_dict(np.asarray(f0['wave']) / 1000, np.asarray(f0['data']) * 10, rsr)

    ## gains
    gains_dict = None
    if gains & (gains_toa is not None):
        if len(gains_toa) == len(rsr_bands):
            gains_dict = {b: float(gains_toa[ib]) for ib, b in enumerate(rsr_bands)}

    global_attrs = {
        'sensor': meta_dict['sensor'], 'satellite_sensor': meta_dict['satellite_sensor'],
        'isodate': isodate,  # 'global_dims':global_dims,
        'sza': meta_dict['sza'], 'vza': meta_dict['vza'], 'raa': meta_dict['raa'], 'se_distance': se_distance,
        'mus': np.cos(meta_dict['sza'] * (np.pi / 180.))
    }

    global_attrs['acolite_file_type'] = 'L1R'

    stime = dateutil.parser.parse(global_attrs['isodate'])

    for b in rsr_bands:
        global_attrs['{}_wave'.format(b)] = waves_mu[b] * 1000
        global_attrs['{}_name'.format(b)] = waves_names[b]
        global_attrs['{}_f0'.format(b)] = f0_b[b]

    dct = projection_read(target_raster.path)

    global_attrs['scene_xrange'] = dct['xrange']
    global_attrs['scene_yrange'] = dct['yrange']
    global_attrs['scene_proj4_string'] = dct['proj4_string']
    global_attrs['scene_pixel_size'] = dct['pixel_size']
    global_attrs['scene_dims'] = dct['dimensions']
    if 'zone' in dct:
        global_attrs['scene_zone'] = dct['zone']

    dct_prj = {k: dct[k] for k in dct}

    if netcdf_projection:
        nc_projection = projection_netcdf(dct_prj, add_half_pixel=True)
    else:
        nc_projection = None

    pkeys = ['xrange', 'yrange', 'proj4_string', 'pixel_size', 'zone']
    for k in pkeys:
        if k in dct_prj:
            global_attrs[k] = dct_prj[k]

    ## warp settings for read_band
    ## updated 2021-10-28
    xyr = [min(dct_prj['xrange']),
           min(dct_prj['yrange']),
           max(dct_prj['xrange']),
           max(dct_prj['yrange']),
           dct_prj['proj4_string']]

    res_method = 'average'
    warp_to = (dct_prj['proj4_string'], xyr, dct_prj['pixel_size'][0], dct_prj['pixel_size'][1], res_method)

    ## store scene and output dimensions
    global_attrs['scene_dims'] = dct['ydim'], dct['xdim']
    global_attrs['global_dims'] = dct_prj['dimensions']

    l1r = init_l1r(dct_prj, output_geolocation=output_geolocation, output_xy=output_xy)
    l1r['bands'] = get_l1r_band(target_raster.bands, rsr_bands)

    return l1r

