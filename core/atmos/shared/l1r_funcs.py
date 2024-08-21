import os
import numpy as np

import core.atmos as atmos
from core.atmos.shared import f0_get
from core.util import rsr_convolute_dict

def get_waves_mu_and_f0(rsr:dict, solar_irradiance_reference) -> tuple:
    waves = np.arange(250, 2500) / 1000
    waves_mu = rsr_convolute_dict(waves, waves, rsr)
    waves_names = {f'{b}': f'{waves_mu[b] * 1000:.0f}' for b in waves_mu}

    f0 = f0_get(f0_dataset=solar_irradiance_reference)
    f0_b = rsr_convolute_dict(wave_data=np.asarray(f0['wave']) / 1000, data=np.asarray(f0['data']) * 10, rsr=rsr)

    return waves, waves_mu, waves_names, f0, f0_b

def load_rsr(sensor:str) -> tuple:

    rsrf = os.path.join(atmos.PROJECT_PATH, 'data', 'atmos', 'RSR', f'{sensor}.txt')
    rsr, rsr_bands = atmos.shared.rsr_read(rsrf)

    return rsr, rsr_bands

def get_gains(gains, gains_toa, rsr_bands) -> dict:

    gains_dict = None
    if gains and (gains_toa is not None):
        if len(gains_toa) == len(rsr_bands):
            gains_dict = {b: float(gains_toa[ib]) for ib, b in enumerate(rsr_bands)}

    return gains_dict

def get_offsets(offsets, offsets_toa, rsr_bands) -> dict:
    offsets_dict = None
    if offsets and (offsets_toa is not None):
        if len(offsets_toa) == len(rsr_bands):
            offsets_dict = {b: float(offsets_toa[ib]) for ib, b in enumerate(rsr_bands)}

    return offsets_dict

def read_tif_meta(path:str) -> dict:
    from osgeo import gdal
    ds = gdal.Open(path)
    tif_meta = ds.GetMetadata_Dict()
    return tif_meta