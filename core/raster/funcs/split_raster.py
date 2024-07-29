from typing import TYPE_CHECKING, Union

from core.raster import Raster, RasterType
from core.raster.funcs import copy_product, copy_ds, set_raw_metadict
from core.util import assert_bnames


def split_raster(raster:Raster, bands_to_split:list[list[Union[str, int]]]=None) -> list[Raster]:

    is_index = False

    if bands_to_split:
        src_bands = raster.get_band_names()
        is_index = all([isinstance(b, int) for b in bands_to_split[0]])

        for b in bands_to_split:
            if is_index:
                bnames = raster.indices_to_band_names(b)
            else:
                bnames = b

            assert_bnames(bnames, src_bands, f'bands list to split {b} should be in source bands({src_bands})')

    if bands_to_split is None:
        bands_to_split = raster.get_band_names()
        bands_to_split = [[b] for b in bands_to_split]

    results = []
    for b in bands_to_split:

        if is_index:
            bnames = raster.indices_to_band_names(b)
            index = b
        else:
            bnames = b
            index = raster.band_names_to_indices(b)

        new_raster = Raster.from_raster(raster)

        if raster.module_type == RasterType.SNAP:
            raw = copy_product(raster.raw, selected_bands=bnames)
        elif raster.module_type == RasterType.GDAL:
            raw = copy_ds(raster.raw, 'MEM', selected_index=index)
        else:
            raise NotImplementedError(f'Raster type {raster.module_type.__str__()} is not implemented')

        new_raster = set_raw_metadict(new_raster, raw, raster.meta_dict, selected_bands=bnames)

        results.append(new_raster)

    return results