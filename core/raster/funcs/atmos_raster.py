from typing import TYPE_CHECKING
from datetime import datetime

from core.util import ProductType

import core.atmos as atmos
from core.atmos.setting import parse

from core.atmos.run import apply_l2r, write_map
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run.sentinel import build_sentinel_l1r
from core.atmos.run.worldview import build_worldview_l1r
from core.atmos.run.planet import build_planet_l1r

if TYPE_CHECKING:
    from core.raster import Raster

def load_user_settings(sensor:str):
    atmos.settings['user'] = parse(sensor=sensor, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    return {k: atmos.settings['run'][k] for k in atmos.settings['run']}


def apply_atmos(target_raster: "Raster", product_type:ProductType, target_band_names:list[str], det_dict:dict, det_names:list[str]) -> dict:

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    set_earthdata_login_to_env(atmos.settings['run'])

    user_settings = load_user_settings(sensor=target_raster.meta_dict['sensor'])

    if product_type == ProductType.S2:
        l1r, l1r_global_attrs = build_sentinel_l1r(target_raster, det_names=det_names, det_dict=det_dict, user_settings=user_settings)
    elif product_type == ProductType.WV:
        l1r, l1r_global_attrs = build_worldview_l1r(target_raster, target_band_names, target_raster.meta_dict, user_settings=user_settings)
    elif product_type == ProductType.PS:
        l1r, l1r_global_attrs = build_planet_l1r(target_raster, target_band_names, target_raster.meta_dict, user_settings=user_settings)
    else:
        raise ValueError(f'Atmospheric correction cannot be applied to {product_type}')

    return apply_l2r(l1r, l1r_global_attrs)

def write_l2r_as_map(l2r:dict, l2r_global_attrs:dict, out_dir:str, out_file_stem:str):

    map_settings = {'rgb_rhot': False, 'rgb_rhorc': False, 'rgb_rhos': True, 'rgb_rhow': False}
    write_map(l2r, out_settings=map_settings, out_file_stem=out_file_stem, out_dir=out_dir, global_attrs=l2r_global_attrs)