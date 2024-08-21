from typing import Union, TYPE_CHECKING
import numpy as np

from core.util import is_contained
from core.raster import RasterType
from core.raster.funcs import read_band_from_raw
from core.util.snap import build_grid_meta_from_gpf
from core.util.gdal import build_grid_meta_from_gdal

if TYPE_CHECKING:
    from core.raster import Raster

def load_det(target_raster: "Raster", det_bands:list[str], size_per_band:dict, det_res:list[int]) -> tuple[dict, list[str]]:

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

def build_det_grid(raster:"Raster", det_names):
    grids = {}
    for det_name in det_names:
        if raster.module_type == RasterType.SNAP:
            grid_dict = build_grid_meta_from_gpf(raster.raw, det_name)
        elif raster.module_type == RasterType.GDAL:
            grid_dict = build_grid_meta_from_gdal(raster.raw)
        else:
            raise NotImplementedError(f'{raster.module_type} is not implemented')
        grids[f'{int(grid_dict["RESOLUTION"])}'] = grid_dict
    return grids