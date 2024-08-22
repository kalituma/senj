from typing import TYPE_CHECKING
from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse

from core.atmos.run import write_map, apply_l2r
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run.sentinel import build_sentinel_l1r
from core.atmos.run.worldview import build_worldview_l1r
from core.atmos.run.planet import build_planet_l1r

if TYPE_CHECKING:
    from core.util import ProductType
    from core.raster import Raster

def load_user_settings(sensor:str):
    atmos.settings['user'] = parse(sensor=sensor, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    return {k: atmos.settings['run'][k] for k in atmos.settings['run']}

def apply_atmos(target_raster: "Raster", product_type:"ProductType", target_band_names:list[str], target_band_slot:list[str], write_png=False, **kwargs):

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    set_earthdata_login_to_env(atmos.settings['run'])

    if product_type == ProductType.S2:
        find_product = lambda x: [field.value for field in parse(x).find(target_raster.meta_dict)]
        s2_mission = '$.Level-1C_User_Product.General_Info.Product_Info.Datatake.SPACECRAFT_NAME'
        craft_name = find_product(s2_mission)[0]
        if craft_name.lower() == 'sentinel-2a':
            user_settings = load_user_settings(sensor='S2A_MSI')
        elif craft_name.lower() == 'sentinel-2b':
            user_settings = load_user_settings(sensor='S2B_MSI')
        else:
            raise ValueError(f'Unknown Sentinel-2 mission: {craft_name}')

        try:
            det_bands = kwargs['det_bands']
        except KeyError:
            raise KeyError('det_bands must be provided for Sentinel-2')

        l1r, l1r_global_attrs = build_sentinel_l1r(target_raster, target_band_names, target_band_slot, det_bands, user_settings=user_settings)

    elif product_type == ProductType.WV:
        user_settings = load_user_settings(sensor=target_raster.meta_dict['sensor'])
        l1r, l1r_global_attrs = build_worldview_l1r(target_raster, target_band_names, target_band_slot,
                                                    target_raster.meta_dict, user_settings=user_settings)
    elif product_type == ProductType.PS:
        user_settings = load_user_settings(sensor=target_raster.meta_dict['sensor'])
        l1r, l1r_global_attrs = build_planet_l1r(target_raster, target_band_names, target_band_slot,
                                                 target_raster.meta_dict, user_settings=user_settings)
    else:
        raise ValueError(f'Atmospheric correction cannot be applied to {product_type}')

    l2r, l2r_global_attrs = apply_l2r(l1r, l1r_global_attrs)

    if write_png:
        try:
            out_dir = kwargs['out_dir']
            out_file_stem = kwargs['out_file_stem']
        except KeyError:
            raise KeyError('out_dir and out_file_stem must be provided if write_png is True')

        map_settings = {'rgb_rhot': False, 'rgb_rhorc': False, 'rgb_rhos': True, 'rgb_rhow': False}
        write_map(l2r, out_settings=map_settings, out_file_stem=out_file_stem, out_dir=out_dir, global_attrs=l2r_global_attrs)



