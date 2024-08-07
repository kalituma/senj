import numpy as np
import dateutil.parser

from core.util import rsr_convolute_dict, distance_se
import core.atmos as atmos
from core.atmos.shared import f0_get
from core.atmos.meta import get_angles_from_meta, get_sensor_type, projection_from_granule_meta, get_gains_offsets_with_rsr, get_waves_mu

def l1r_meta_to_global_attrs(l1r_meta:dict) -> tuple[dict, dict]:

    assert l1r_meta['product_info']['PROCESSING_LEVEL'] == 'Level-1C', 'Input data is not Level-1C.'
    user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}

    sensor = get_sensor_type(l1r_meta['product_info'])

    dtime = dateutil.parser.parse(l1r_meta['granule_meta']['SENSING_TIME'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    user_settings = atmos.setting.parse(sensor, settings=user_settings)

    proj_dict = projection_from_granule_meta(l1r_meta['granule_meta'], s2_target_res=user_settings['s2_target_res'])

    sza, saa, vza, vaa, raa = get_angles_from_meta(l1r_meta['granule_meta'])

    rsr, rsr_bands, gains_dict, offsets_dict = get_gains_offsets_with_rsr(
        sensor=sensor, gains=user_settings['gains'], gains_toa=user_settings['gains_toa'],
        offsets=user_settings['offsets'], offsets_toa=user_settings['offsets_toa'])

    waves, w_mu, w_names = get_waves_mu(rsr)

    f0 = f0_get(f0_dataset=user_settings['solar_irradiance_reference'])
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

    global_attrs['index_to_band'] = rsr_bands
    global_attrs['proj_dict'] = proj_dict
    global_attrs['wave_names'] = w_names
    global_attrs['wave_mu'] = w_mu
    global_attrs['gains_dict'] = gains_dict
    global_attrs['offsets_dict'] = offsets_dict

    return global_attrs, user_settings