from typing import TYPE_CHECKING, Union

from core.raster import Raster
from core.raster.funcs import select_band_raster

def split_raster(raster:Raster, bands_to_split:list[list[Union[str, int]]]=None) -> list[Raster]:

    if bands_to_split is None:
        bands_to_split = raster.get_band_names()
        bands_to_split = [[b] for b in bands_to_split]

    results = []
    for b in bands_to_split:
        new_raster = select_band_raster(raster, b)
        results.append(new_raster)

    return results