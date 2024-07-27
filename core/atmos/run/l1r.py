from typing import Union, TYPE_CHECKING
import os
from datetime import datetime

import core.atmos as atmos
from core.atmos.setting import parse
from core.raster.gpf_module import find_granules_meta, get_size_meta_per_band_gpf
from core.raster import RasterType

if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo import gdal
    from core.raster import Raster

def prepare_meta(raster:"Raster", selected_bands) -> dict:
    meta_dict = raster.meta_dict


    granule_meta = find_granules_meta(meta_dict)
    if raster.module_type == RasterType.SNAP:
        size_meta_per_band = get_size_meta_per_band_gpf(raster.raw, selected_bands)

    reflect_meta = get_reflectance_meta(meta_dict)
    band_meta = get_band_info_meta(meta_dict)

    return {
        'granule_meta': granule_meta,
        'size_meta_per_band': size_meta_per_band,
        'reflect_meta': reflect_meta,
        'band_meta': band_meta
    }

def build_l1r(bands:dict, det_bands:dict, meta_dict:dict, percentiles_compute=True, percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    setu = {k: atmos.settings['run'][k] for k in atmos.settings['run']}
    granule_meta = find_granules_meta(meta_dict)
    size_meta_per_band = get_size_meta_per_band_gpf(bands['raw'])
