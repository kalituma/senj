from typing import TYPE_CHECKING
from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run.sentinel import build_sentinel_l1r

if TYPE_CHECKING:
    from core.util import ProductType
    from core.raster import Raster


def apply_atmos(target_raster: "Raster", product_type:"ProductType", target_band_names:list[str], target_band_slot:list[str],
                atmos_conf_path:str, **kwargs):

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    atmos.settings['user'] = parse(None, atmos_conf_path, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    set_earthdata_login_to_env(atmos.settings['run'])
    user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}

    if product_type == ProductType.S2:
        det_bands = kwargs['det_bands']
        l1r, global_attrs = build_sentinel_l1r(target_raster, target_band_names, target_band_slot, det_bands, user_settings=user_settings)

    return l1r, global_attrs


