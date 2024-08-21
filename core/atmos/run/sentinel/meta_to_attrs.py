import numpy as np
import dateutil.parser

from core.util import distance_se
import core.atmos as atmos
from core.atmos.shared import get_waves_mu_and_f0, load_rsr, get_gains, get_offsets
from core.atmos.run.sentinel import get_sensor_type, projection_from_granule_meta


def get_angles_from_meta(granule_meta:dict):
    sza = granule_meta['SUN']['Mean_Zenith']
    saa = granule_meta['SUN']['Mean_Azimuth']
    vza = np.nanmean(granule_meta['VIEW']['Average_View_Zenith'])
    vaa = np.nanmean(granule_meta['VIEW']['Average_View_Azimuth'])
    raa = np.abs(saa - vaa)
    while raa > 180:
        raa = np.abs(360 - raa)

    return sza, saa, vza, vaa, raa

def l1r_meta_to_global_attrs(l1r_meta:dict, user_settings:dict) -> tuple[dict, dict]:

    assert l1r_meta['product_info']['PROCESSING_LEVEL'] == 'Level-1C', 'Input data is not Level-1C.'

    sensor = get_sensor_type(l1r_meta['product_info'])

    dtime = dateutil.parser.parse(l1r_meta['granule_meta']['SENSING_TIME'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    user_settings = atmos.setting.parse(sensor, settings=user_settings)

    proj_dict = projection_from_granule_meta(l1r_meta['granule_meta'], s2_target_res=user_settings['s2_target_res'])

    sza, saa, vza, vaa, raa = get_angles_from_meta(l1r_meta['granule_meta'])
    rsr, rsr_bands = load_rsr(sensor)
    gains_dict = get_gains(user_settings['gains'], user_settings['gains_toa'], rsr_bands)
    offsets_dict = get_offsets(user_settings['offsets'], user_settings['offsets_toa'], rsr_bands)

    waves, w_mu, w_names, f0, f0_b = get_waves_mu_and_f0(rsr, user_settings['solar_irradiance_reference'])

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