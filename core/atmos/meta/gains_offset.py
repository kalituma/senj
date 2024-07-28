import os
import numpy as np

import core.atmos as atmos
from core.util import rsr_convolute_dict

def get_waves_mu(rsr:dict) -> tuple:
    waves = np.arange(250, 2500) / 1000
    waves_mu = rsr_convolute_dict(waves, waves, rsr)
    waves_names = {f'{b}': f'{waves_mu[b] * 1000:.0f}' for b in waves_mu}

    return waves, waves_mu, waves_names

def get_gains_offsets_with_rsr(sensor:str, gains, gains_toa, offsets, offsets_toa) -> tuple:

    rsrf = os.path.join(atmos.PROJECT_PATH, 'data', 'atmos', 'RSR', f'{sensor}.txt')
    rsr, rsr_bands = atmos.shared.rsr_read(rsrf)

    gains_dict = None
    if gains & (gains_toa is not None):
        if len(gains_toa) == len(rsr_bands):
            gains_dict = {b: float(gains_toa[ib]) for ib, b in enumerate(rsr_bands)}

    offsets_dict = None
    if offsets & (offsets_toa is not None):
        if len(offsets_toa) == len(rsr_bands):
            offsets_dict = {b: float(offsets_toa[ib]) for ib, b in enumerate(rsr_bands)}

    return rsr, rsr_bands, gains_dict, offsets_dict