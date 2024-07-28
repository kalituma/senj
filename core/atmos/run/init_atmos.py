from typing import Union, TYPE_CHECKING

from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse

from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run import extract_l1r_meta, transform_l1r_meta_to_global_attrs, build_l1r

if TYPE_CHECKING:
    from core.raster import Raster

def init_atmos(target_raster: "Raster", band_dict:dict, det_dict:dict, atmos_conf_path, selected_bands:list[str]=None):

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    atmos.settings['user'] = parse(None, atmos_conf_path, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    set_earthdata_login_to_env(atmos.settings['run'])

    # read_det(product, selected_bands)
    l1r_meta = extract_l1r_meta(target_raster, selected_bands)
    l1r = build_l1r(band_dict, det_dict, l1r_meta)


