from typing import Union, TYPE_CHECKING
import numpy as np

from core.util import is_contained
from core.raster import ModuleType
from core.raster.funcs import read_band_from_raw
from core.util.snap import build_grid_meta_from_gpf
from core.util.gdal import build_grid_meta_from_gdal

if TYPE_CHECKING:
    from core.raster import Raster

def build_det_grid(raster:"Raster", det_names):
    grids = {}
    for det_name in det_names:
        if raster.module_type == ModuleType.SNAP:
            grid_dict = build_grid_meta_from_gpf(raster.raw, det_name)
        elif raster.module_type == ModuleType.GDAL:
            grid_dict = build_grid_meta_from_gdal(raster.raw)
        else:
            raise NotImplementedError(f'{raster.module_type} is not implemented')
        grids[f'{int(grid_dict["RESOLUTION"])}'] = grid_dict
    return grids