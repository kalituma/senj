from typing import TYPE_CHECKING

from core.raster import Raster, RasterType
from core.raster.funcs import copy_product, copy_ds
from core.util import assert_bnames


def split_raster(raster:Raster, bands_to_split:list[list[str]]=None) -> list[Raster]:

    if bands_to_split:
        src_bands = raster.get_band_names()
        for b in bands_to_split:
            assert_bnames(b, src_bands, f'bands list to split {b} should be in source bands({src_bands})')

    if bands_to_split is None:
        bands_to_split = raster.get_band_names()
        bands_to_split = [[b] for b in bands_to_split]

    results = []
    for b in bands_to_split:
        new_raster = Raster.from_raster(raster)

        if raster.module_type == RasterType.SNAP:
            new_raster.raw = copy_product(raster.raw, b)
        elif raster.module_type == RasterType.GDAL:
            new_raster.raw = copy_ds(raster.raw, 'MEM', b)
        else:
            raise NotImplementedError(f'Raster type {raster.module_type.__str__()} is not implemented')

        results.append(new_raster)

    return results