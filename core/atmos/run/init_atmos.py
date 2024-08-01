from typing import Union, TYPE_CHECKING

from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse

from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run import build_l1r
from core.atmos.run.l1r import meta_dict_to_l1r_meta

if TYPE_CHECKING:
    from core.raster import Raster

def apply_atmos(target_raster: "Raster", target_band_names:list[str], target_det_name:str, target_band_slot:list[str], atmos_conf_path:str):

    assert len(target_band_names) == len(target_band_slot), 'Band names and slots should have the same length.'

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    atmos.settings['user'] = parse(None, atmos_conf_path, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    set_earthdata_login_to_env(atmos.settings['run'])

    l1r_meta = meta_dict_to_l1r_meta(target_raster)

    # todo: load band to cache if it is not already loaded
    band_dict = {bslot: target_raster[bname] for bname, bslot in zip(target_band_names, target_band_slot)}
    det_band = target_raster[target_det_name]['value']
    det_size = l1r_meta['size_meta_per_band'][target_det_name]

    # read_det(product, selected_bands)
    l1r, global_attrs = build_l1r(bands=band_dict, det_band=det_band, det_size=det_size, l1r_meta=l1r_meta)

    return l1r, global_attrs
    # apply l2r



