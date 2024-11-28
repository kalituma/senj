import numpy as np

def calculate_back_coef(bands:dict):

    for key, value in bands.items():
        band = value['value']
        band[band <= 0] = np.min(band[band > 0])
        value['value'] = 10 * np.log10(band)

    return bands