import numpy as np
from core.util import Logger
def clip_angles(l1r, l1r_band_list, user_settings):
    sza_limit = user_settings['sza_limit']
    sza_limit_replace = user_settings['sza_limit_replace']

    if 'sza' in l1r_band_list:

        Logger.get_logger().log('info','Warning: SZA out of LUT range')
        Logger.get_logger().log('info',f'Mean SZA: {np.nanmean(l1r["sza"]):.3f}')
        if sza_limit_replace:
            l1r['sza'] = np.clip(l1r['sza'], max=sza_limit)

    return l1r

def clip_angles_mean(geom_mean:dict, user_settings:dict):

    def _load_params():
        sza_limit = user_settings['sza_limit']
        vza_limit = user_settings['vza_limit']
        sza_limit_replace = user_settings['sza_limit_replace']
        vza_limit_replace = user_settings['vza_limit_replace']
        return sza_limit, vza_limit, sza_limit_replace, vza_limit_replace

    sza_limit, vza_limit, sza_limit_replace, vza_limit_replace = _load_params()

    if geom_mean['sza'] > sza_limit:
        Logger.get_logger().log('info','Warning: SZA out of LUT range')
        Logger.get_logger().log('info',f'Mean SZA: {geom_mean["sza"]:.3f}')
        if sza_limit_replace:
            geom_mean['sza'] = sza_limit
            Logger.get_logger().log('info',f'Mean SZA after replacing SZA > {user_settings["sza_limit"]}: {geom_mean["sza"]:.3f}')

    if geom_mean['vza'] > vza_limit:
        Logger.get_logger().log('info','Warning: VZA out of LUT range')
        Logger.get_logger().log('info',f'Mean VZA: {geom_mean["vza"]:.3f}')
        if vza_limit_replace:
            geom_mean['vza'] = vza_limit
            Logger.get_logger().log('info',f'Mean VZA after replacing VZA > {user_settings["vza_limit"]}: {geom_mean["vza"]:.3f}')

    return geom_mean