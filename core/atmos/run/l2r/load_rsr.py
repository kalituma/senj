import core.atmos as atmos
from atmos.shared import rsr_dict, rsr_hyper

def load_rsrd(global_attrs:dict) -> tuple:

    is_hyper = False
    ## hyperspectral
    if global_attrs['sensor'] in atmos.config['hyper_sensors']:
        is_hyper = True
        rsr = rsr_hyper(global_attrs['band_waves'], global_attrs['band_widths'], step=0.1)
        rsrd = rsr_dict(rsrd={global_attrs['sensor']: {'rsr': rsr}})
        del rsr
    else:
        rsrd = rsr_dict(global_attrs['sensor'])

    return rsrd, is_hyper