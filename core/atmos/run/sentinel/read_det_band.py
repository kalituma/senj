from typing import Union, TYPE_CHECKING
import numpy as np

from core.util import is_contained
from core.raster.funcs import read_band_from_raw

if TYPE_CHECKING:
    from core.raster import Raster

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