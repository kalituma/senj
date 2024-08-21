import os

import core.atmos as atmos
from core import ATMOS_SCRATCH_PATH
from util import polygon_from_wkt

def set_l2w_and_polygon(user_settings:dict) -> dict:

    if 'l2w_parameters' in user_settings:
        if user_settings['l2w_parameters'] is not None:
            if type(user_settings['l2w_parameters']) is not list:
                user_settings['l2w_parameters'] = [user_settings['l2w_parameters']]
            for par in user_settings['l2w_parameters']:
                if 'rhorc' in par:
                    user_settings['output_rhorc'] = True
                if 'bt' == par[0:2]:
                    user_settings['output_bt'] = True

    if 'polygon' in user_settings:
        if user_settings['polygon'] is not None:
            if not os.path.exists(user_settings['polygon']):
                try:
                    polygon_new = polygon_from_wkt(user_settings['polygon'], file =f'{ATMOS_SCRATCH_PATH}/polygon_{atmos.settings["run"]["runid"]}.json')
                    user_settings['polygon_old'] = '{}'.format(user_settings['polygon'])
                    user_settings['polygon'] = '{}'.format(polygon_new)
                except:
                    print('Provided polygon is not a valid WKT polygon')
                    print(user_settings['polygon'])
                    user_settings['polygon'] = None
                    pass

    return user_settings

def set_verbosity_to_config(run_settings:dict):
    if 'verbosity' in run_settings:
        atmos.config['verbosity'] = int(run_settings['verbosity'])

def update_user_to_run(run_settings:dict, user_settings:dict) -> dict:
    for k in user_settings:
        if k in run_settings:
            run_settings[k] = user_settings[k]
    return run_settings

def set_earthdata_login_to_env(run_settings:dict):
    for k in ['EARTHDATA_u', 'EARTHDATA_p']:
        kv = run_settings[k] if k in run_settings else atmos.config[k]
        if len(kv) == 0: continue
        os.environ[k] = kv

