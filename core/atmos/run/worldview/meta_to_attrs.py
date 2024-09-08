import numpy as np
import dateutil.parser

from core.util import distance_se, Logger
from core.atmos.shared import get_waves_mu_and_f0, load_rsr

def get_angles_from_meta(mean_sun_azimuth, mean_sat_azimuth,
                         mean_sun_el, mean_sat_el):
    raa = abs(float(mean_sun_azimuth) - float(mean_sat_azimuth))
    while raa >= 180.: raa = np.abs(raa - 360)
    sza = 90. - float(mean_sun_el)
    vza = 90. - float(mean_sat_el)

    return sza, vza, raa

def meta_dict_to_global_attrs(meta_dict:dict, user_settings:dict, atmospherically_corrected:bool) -> dict:

    sza, vza, raa = get_angles_from_meta(meta_dict['MEANSUNAZ'], meta_dict['MEANSATAZ'], meta_dict['MEANSUNEL'], meta_dict['MEANSATEL'])

    dtime = dateutil.parser.parse(meta_dict['isotime'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    rsr, rsr_bands = load_rsr(meta_dict['sensor'])
    rsr_bands = [b.lower() for b in rsr_bands]
    rsr = {b.lower(): rsr[b] for b in rsr}
    waves, waves_mu, waves_names, f0, f0_b = get_waves_mu_and_f0(rsr, user_settings['solar_irradiance_reference'])

    gains = None
    if user_settings['gains']:
        if len(user_settings['gains_toa']) == len(rsr_bands) and len(user_settings['offsets_toa']) == len(rsr_bands):
            gains = {}
            for bi, band in enumerate(rsr_bands):
                gains[band] = {'gain': float(user_settings['gains_toa'][bi]),
                               'offset': float(user_settings['offsets_toa'][bi])}
        else:
            Logger.get_logger().log('info', f"Use of gains requested, but provided number of gain ({user_settings['gains_toa']}) or \
                                 offset ({user_settings['offsets_toa']}) values does not match number of bands in RSR ({len(rsr_bands)})")
            Logger.get_logger().log('info', f'Provide gains in band order: {",".join(rsr_bands)}')

    global_attrs = {
        'sensor': meta_dict['sensor'], 'satellite': meta_dict['satellite'],
        'isodate': isodate,  # 'global_dims':global_dims,
        'sza': sza, 'vza': vza, 'raa': raa, 'se_distance': se_distance,
        'mus': np.cos(sza * (np.pi / 180.)), 'acolite_file_type': 'L1R',
        'gains': gains, 'f0_b': f0_b, 'waves_mu': waves_mu, 'waves_names': waves_names
    }

    if atmospherically_corrected:
        global_attrs['acolite_file_type'] = 'converted'

    # skip the part for output specification
    ## add band info to gatts
    for b in rsr_bands:
        global_attrs[f'{b}_wave'] = waves_mu[b] * 1000
        global_attrs[f'{b}_name'] = waves_names[b]
        global_attrs[f'{b}_f0'] = f0_b[b]

    return global_attrs