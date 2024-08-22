import numpy as np
from atmos.shared import closest_idx

def check_blackfill_skip(l1r_bands:dict, user_settings:dict):

    rhot_wv = [int(l1r_bands[key]['att']['parameter'].split('_')[-1]) for key in l1r_bands.keys()]  ## use last element of rhot name as wavelength
    bi, bw = closest_idx(rhot_wv, user_settings['blackfill_wave'])
    closest_bkey = list(l1r_bands.keys())[bi]

    blackfill_target = 1.0 * l1r_bands[closest_bkey]['data']
    npx = blackfill_target.shape[0] * blackfill_target.shape[1]
    # nbf = npx - len(np.where(np.isfinite(band_data))[0])
    nbf = npx - len(np.where(np.isfinite(blackfill_target) * (blackfill_target > 0))[0])
    del blackfill_target

    if (nbf / npx) >= float(user_settings['blackfill_max']):
        return True

    return False