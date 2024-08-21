from typing import Union

from core.raster import Raster, RasterType
from core.util import assert_bnames
from core.util.snap import merge as merge_gpf
from core.util.gdal import merge as merge_gdal

def merge_raster_func(rasters:list[Raster], co_bands:Union[list[list[Union[str, int]]], None]=None):

    if co_bands:
        assert len(rasters) == len(co_bands), 'The number of rasters and selected bands must be the same'
        for raster, co_band in zip(rasters, co_bands):
            assert_bnames(co_band, raster.get_band_names(), f'selected bands({co_band}) not found in raster{raster.path}')
    else:
        co_bands = [None for _ in rasters]

    assert all([r.module_type == rasters[0].module_type for r in rasters]), 'all rasters should have the same module type'

    raw_list = [r.raw for r in rasters]
    sband_list = [r.selected_bands for r in rasters]

    if rasters[0].module_type == RasterType.GDAL:
        merged = merge_gdal(raw_list, sband_list, co_bands)
    elif rasters[0].module_type == RasterType.SNAP:
        merged = merge_gpf(raw_list, sband_list, co_bands)
    else:
        raise NotImplementedError(f'Raster type {rasters[0].module_type} is not implemented')

    merged_raster = Raster.from_raster(rasters[0], path='', raw=merged, selected_bands=None)

    return merged_raster