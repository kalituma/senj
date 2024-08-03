import numpy as np

def clip_angles(l1r_band_list:list, l1r:dict, geom_mean:dict, user_settings:dict):

    if 'sza' in l1r_band_list:
        # print('Warning: SZA out of LUT range')
        # print(f'Mean SZA: {np.nanmean(sza):.3f}')
        if user_settings['sza_limit_replace']:
            l1r['sza'] = np.clip(l1r['sza'], max=user_settings['sza_limit'])

    if geom_mean['sza'] > user_settings['sza_limit']:
        # print('Warning: SZA out of LUT range')
        # print(f'Mean SZA: {geom_mean["sza"]:.3f}')
        if (user_settings['sza_limit_replace']):
            geom_mean['sza'] = user_settings['sza_limit']
            # print(f'Mean SZA after replacing SZA > {user_settings["sza_limit"]}: {geom_mean["sza"]:.3f}')

    if geom_mean['vza'] > user_settings['vza_limit']:
        # print('Warning: VZA out of LUT range')
        # print(f'Mean VZA: {geom_mean["vza"]:.3f}')
        if user_settings['vza_limit_replace']:
            geom_mean['vza'] = user_settings['vza_limit']
            # print(f'Mean VZA after replacing VZA > {user_settings["vza_limit"]}: {geom_mean["vza"]:.3f}')

    return l1r, geom_mean