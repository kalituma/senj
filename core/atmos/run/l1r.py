import numpy as np
from typing import Union, TYPE_CHECKING
import dateutil.parser
from datetime import datetime


from core.raster import RasterType
import core.atmos as atmos
from core.util import distance_se, rsr_convolute_dict, tiles_interp, grid_extend, distance_se, projection_geo
from core.atmos.shared import f0_get

from core.atmos.meta import get_angles_from_meta, get_sensor_type, \
    projection_from_granule_meta, get_gains_offsets_with_rsr, get_waves_mu

from core.raster.gpf_module import find_grids_and_angle_meta, get_size_meta_per_band_gpf, \
    get_product_info_meta, get_band_info_meta, get_granule_info
from core.raster.gdal_module import get_size_meta_per_band_gdal

if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo import gdal
    from core.raster import Raster

def extract_l1r_meta(raster: "Raster", selected_bands=None) -> dict:

    assert raster.meta_dict, 'Raster meta data is not available.'

    meta_dict = raster.meta_dict

    granule_info = get_granule_info(meta_dict)
    granule_meta = find_grids_and_angle_meta(meta_dict) # Grid, Sun, View
    granule_meta['granule_info'] = granule_info

    if raster.module_type == RasterType.SNAP:
        size_meta_per_band = get_size_meta_per_band_gpf(raster.raw, selected_bands)
    elif raster.module_type == RasterType.GDAL:
        size_meta_per_band = get_size_meta_per_band_gdal(raster.raw, selected_bands)
    else:
        raise NotImplementedError(f'{raster.module_type} is not implemented.')

    product_info = get_product_info_meta(meta_dict) # Time, Spacecraft, Orbit
    sensor_response = get_band_info_meta(meta_dict) # Wavelength, RSR

    return {
        'granule_meta': granule_meta,
        'size_meta_per_band': size_meta_per_band,
        'product_info': product_info,
        'sensor_response': sensor_response
    }

def transform_l1r_meta_to_global_attrs(l1r_meta:dict) -> tuple[dict, dict]:

    assert l1r_meta['product_info']['PROCESSING_LEVEL'] == 'Level-1C', 'Input data is not Level-1C.'

    setu = {k: atmos.settings['run'][k] for k in atmos.settings['run']}

    sensor = get_sensor_type(l1r_meta['product_info'])


    dtime = dateutil.parser.parse(l1r_meta['granule_meta']['SENSING_TIME'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    setu = atmos.setting.parse(sensor, settings=setu)

    proj_dict = projection_from_granule_meta(l1r_meta['granule_meta'], s2_target_res=int(setu['s2_target_res']))

    sza, saa, vza, vaa, raa = get_angles_from_meta(l1r_meta['granule_meta'])

    rsr, rsr_bands, gains_dict, offsets_dict = get_gains_offsets_with_rsr(
        sensor=sensor, gains=setu['gains'], gains_toa=setu['gains_toa'],
        offsets=setu['offsets'], offsets_toa=setu['offsets_toa'])

    waves, w_mu, w_names = get_waves_mu(rsr)

    f0 = f0_get(f0_dataset=setu['solar_irradiance_reference'])
    f0_b = rsr_convolute_dict(wave_data=np.asarray(f0['wave']) / 1000, data=np.asarray(f0['data']) * 10, rsr=rsr)

    global_attrs = {
        'sensor': sensor, 'isodate': isodate, 'global_dims': proj_dict['dimensions'],
        'sza': sza, 'vza': vza, 'raa': raa, 'vaa': vaa, 'saa': saa, 'se_distance': se_distance,
        'mus': np.cos(sza * (np.pi / 180.)), 'granule': l1r_meta['granule_meta']['granule_info'],
        'mgrs_tile': l1r_meta['granule_meta']['TILE_ID'].split('_')[-2],
        'acolite_file_type': 'L1R'
    }

    for b in rsr_bands:
        global_attrs['{}_wave'.format(b)] = w_mu[b] * 1000
        global_attrs['{}_name'.format(b)] = w_names[b]
        global_attrs['{}_f0'.format(b)] = f0_b[b]

    global_attrs['scene_xrange'] = proj_dict['xrange']
    global_attrs['scene_yrange'] = proj_dict['yrange']
    global_attrs['scene_proj4_string'] = proj_dict['proj4_string']
    global_attrs['scene_pixel_size'] = proj_dict['pixel_size']
    global_attrs['scene_dims'] = proj_dict['dimensions']

    if 'zone' in proj_dict:
        global_attrs['scene_zone'] = proj_dict['zone']

    return global_attrs, setu

def build_l1r(bands:dict, det_bands:dict, l1r_meta:dict,
                                       percentiles_compute=True,
                                       percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    assert bands.keys() == det_bands.keys(), 'Band and detector band keys do not match.'

    global_attrs, user_settings = transform_l1r_meta_to_global_attrs(l1r_meta)

    warp_option_for_angle = (
        global_attrs['scene_proj4_string'],
        [
            min(global_attrs['scene_xrange']), min(global_attrs['scene_yrange']),
            max(global_attrs['scene_xrange']), max(global_attrs['scene_yrange'])
        ],
        global_attrs['scene_pixel_size'][0],
        global_attrs['scene_pixel_size'][1],
        'average' # resampling method
    )

    granule_meta = l1r_meta['granule_meta']
    geometry_res = user_settings['geometry_res']

    # build angle
    # build_