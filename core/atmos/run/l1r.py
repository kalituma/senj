import os
from datetime import datetime
from esa_snappy import Product

import core.atmos as atmos
from core.atmos.setting import parse

def build_l1r(bands:dict, det_bands:dict, percentiles_compute=True, percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    setu = {k: atmos.settings['run'][k] for k in atmos.settings['run']}

