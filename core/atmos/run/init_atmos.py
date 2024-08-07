from typing import Union, TYPE_CHECKING
from datetime import datetime
from fnmatch import fnmatch

import numpy as np

import core.atmos as atmos
from core.atmos.setting import parse
from core.raster.funcs import read_band_from_raw, build_det_grid

from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env
from core.atmos.run import build_l1r
from core.atmos.run.l1r import meta_dict_to_l1r_meta

if TYPE_CHECKING:
    from core.raster import Raster

def is_contained(target_list:list, src_list:list):
    return all([t in src_list for t in target_list])

def glob_match(str_list:list[str], pattern:str):
    return [s for s in str_list if fnmatch(s, pattern)]

def read_det(target_raster: "Raster", det_bands:list[str], size_per_band:dict, det_res:list[int]) -> tuple[dict, list[str]]:

    det_res_map = {}

    try:
        for det_bname in det_bands:
            res = int(size_per_band[det_bname]['x_res'])
            if res in det_res and res not in det_res_map:
                det_res_map[f'{res}'] = det_bname
    except KeyError:
        raise ValueError(f'No matching band found in target raster: {det_bname}')

    assert len(det_res_map) == len(det_res), 'Detectors should have the same resolution.'

    # target_bands = target_bands + [target_det]
    target_raster = read_band_from_raw(target_raster, selected_band=list(det_res_map.values()))

    for res, det_bname in det_res_map.items():
        det_elems = np.unique(target_raster[det_bname]['value']).tolist()
        assert is_contained(det_elems, src_list=[2,3,4,5,6,7]), 'Detector band should have values from 2 to 7.'

    det_dict = {res: target_raster[det_bname]['value'] for res, det_bname in det_res_map.items()}

    return det_dict, list(det_res_map.values())

def read_bands(target_raster:"Raster", target_band_names:list[str], target_band_slot:list[str]) -> "Raster":

    assert len(target_band_names) == len(target_band_slot), 'Length of target_band_names and target_band_slot should be the same.'

    target_raster = read_band_from_raw(target_raster, target_band_names)

    for bname, bslot in zip(target_band_names, target_band_slot):
        target_raster[bname]['slot'] = bslot

    return target_raster

def apply_atmos(target_raster: "Raster", target_band_names:list[str], target_band_slot:list[str], det_bands:Union[str, list[str]], atmos_conf_path:str):

    time_start = datetime.now()
    atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
    atmos.settings['user'] = parse(None, atmos_conf_path, merge=False)
    atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
    atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
    set_earthdata_login_to_env(atmos.settings['run'])

    l1r_meta = meta_dict_to_l1r_meta(target_raster)

    res_set = set()
    for bname in target_band_names:
        x_res = int(l1r_meta['size_meta_per_band'][bname]['x_res'])
        if x_res not in res_set:
            res_set.add(x_res)

    all_bands = target_raster.get_band_names()
    if isinstance(det_bands, str):
        # find the band with glob pattern with asterisk described in det_bands
        det_bands = glob_match(all_bands, det_bands)
    elif isinstance(det_bands, list):
        det_bands = det_bands
    else:
        raise ValueError('det_bands should be either a string or a list of strings.')

    assert len(det_bands) > 0, 'No matching band found in target raster.'

    det_dict, det_names = read_det(target_raster, det_bands=det_bands, size_per_band=l1r_meta['size_meta_per_band'], det_res=list(res_set))

    target_raster = read_bands(target_raster, target_band_names, target_band_slot)

    det_sizes = { det_name : l1r_meta['size_meta_per_band'][det_name] for det_name in det_names}
    l1r_meta['granule_meta']['GRIDS'] = build_det_grid(target_raster, det_names)

    # todo: load band to cache if it is not already loaded
    l1r, global_attrs = build_l1r(bands=target_raster.bands, det_dict=det_dict, det_sizes=det_sizes, l1r_meta=l1r_meta)

    return l1r, global_attrs
    # apply l2r



