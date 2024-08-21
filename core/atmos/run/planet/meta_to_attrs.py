import numpy as np
import dateutil.parser
from core.util import distance_se
from core.atmos.shared import get_waves_mu_and_f0, load_rsr, get_gains

def meta_dict_to_global_attrs(meta_dict:dict, user_settings:dict) -> dict:

    dtime = dateutil.parser.parse(meta_dict['isotime'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    rsr, rsr_bands = load_rsr(meta_dict['sensor'])
    rsr_bands = [b.lower() for b in rsr_bands]
    rsr = {b.lower(): rsr[b] for b in rsr}
    waves, waves_mu, waves_names, f0, f0_b = get_waves_mu_and_f0(rsr, user_settings['solar_irradiance_reference'])

    ## gains
    gains_dict = get_gains(user_settings['gains'], user_settings['gains_toa'], rsr_bands)

    global_attrs = {
        'sensor': meta_dict['sensor'], 'satellite_sensor': meta_dict['satellite_sensor'],
        'isodate': isodate,  # 'global_dims':global_dims,
        'sza': meta_dict['sza'], 'vza': meta_dict['vza'], 'raa': meta_dict['raa'], 'se_distance': se_distance,
        'mus': np.cos(meta_dict['sza'] * (np.pi / 180.)), 'gains_dict': gains_dict,
        'wave_names': waves_names, 'wave_mu': waves_mu, 'f0': f0, 'f0_b': f0_b
    }

    global_attrs['acolite_file_type'] = 'L1R'

    for b in rsr_bands:
        global_attrs[f'{b}_wave'] = waves_mu[b] * 1000
        global_attrs[f'{b}_name'] = waves_names[b]
        global_attrs[f'{b}_f0'] = f0_b[b]

    return global_attrs



