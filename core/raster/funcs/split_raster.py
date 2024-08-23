from typing import TYPE_CHECKING, Union

from core.raster import Raster, RasterType
from core.raster.funcs import copy_product, copy_ds, set_raw_metadict, update_meta_band_map, get_band_name_and_index
from core.util import assert_bnames

def split_raster(raster:Raster, bands_to_split:list[list[Union[str, int]]]=None) -> list[Raster]:

    if bands_to_split:
        src_bands = raster.get_band_names()

        for b in bands_to_split:
            band_name, index = get_band_name_and_index(raster, b)
            assert_bnames(band_name, src_bands, f'bands list to split {b} should be in source bands({src_bands})')

    if bands_to_split is None:
        bands_to_split = raster.get_band_names()
        bands_to_split = [[b] for b in bands_to_split]

    results = []
    for b in bands_to_split:

        band_name, index = get_band_name_and_index(raster, b)
        new_raster = Raster.from_raster(raster)

        if raster.module_type == RasterType.SNAP:
            raw = copy_product(raster.raw, selected_bands=band_name)
        elif raster.module_type == RasterType.GDAL:
            raw = copy_ds(raster.raw, 'MEM', selected_index=index)
        else:
            raise NotImplementedError(f'Raster type {raster.module_type.__str__()} is not implemented')

        if raster.meta_dict:
            new_meta = update_meta_band_map(raster.meta_dict, band_name)
        else:
            new_meta = None

        new_raster = set_raw_metadict(new_raster, raw, new_meta, selected_bands=band_name)

        results.append(new_raster)

    return results