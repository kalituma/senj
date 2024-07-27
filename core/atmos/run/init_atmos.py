from typing import Union

from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse


from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run import build_l1r

def init_atmos(bands:dict, det:dict, meta_dict:dict, atmos_conf_path):

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    atmos.settings['user'] = parse(None, atmos_conf_path, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    set_earthdata_login_to_env(atmos.settings['run'])

    # read_det(product, selected_bands)
    build_l1r(bands, det, meta_dict)



