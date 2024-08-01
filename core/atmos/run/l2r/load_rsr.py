import core.atmos as atmos
from atmos.shared import rsr_dict, rsr_hyper

def load_rsrd(gloabl_settings:dict) -> tuple:

    is_hyper = False
    ## hyperspectral
    if gloabl_settings['sensor'] in atmos.config['hyper_sensors']:
        is_hyper = True
        rsr = rsr_hyper(gloabl_settings['band_waves'], gloabl_settings['band_widths'], step=0.1)
        rsrd = rsr_dict(rsrd={gloabl_settings['sensor']: {'rsr': rsr}})
        del rsr
    else:
        rsrd = rsr_dict(gloabl_settings['sensor'])

    return rsrd, is_hyper