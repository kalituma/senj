from typing import List, AnyStr
from pathlib import Path

from core.util import set_btoi_to_tif
from core.util.snap import rename_bands
from core.raster import Raster, ModuleType
from core.raster.funcs import get_band_name_and_index
from core.raster.funcs.meta import MetaBandsManager

def rename_raster_bands(raster:Raster, old_names_or_indices:List[AnyStr], new_band_names:List[AnyStr]):
    assert len(new_band_names) == len(old_names_or_indices), f'new band names({len(new_band_names)}) should be equal to the number of bands({len(raster.bands)})'

    path = raster.path
    old_names, old_indices = get_band_name_and_index(raster, old_names_or_indices)
    old_to_new = {old:new for old, new in zip(old_names, new_band_names)}
    band_name_list = raster.get_band_names()

    for i in range(len(band_name_list)):
        if band_name_list[i] in old_to_new:
            band_name_list[i] = old_to_new[band_name_list[i]]

    # if path != '':
    #     ext = Path(path).suffix[1:].lower()
    #     if ext == 'tif':
    #         raster.raw = set_btoi_to_tif(path, {band_name_list[i]:i+1 for i in range(len(band_name_list))})

    MetaBandsManager(raster).update_band_mapping(band_name_list)

    if raster.module_type == ModuleType.SNAP:
        raster.raw = rename_bands(raster.raw, band_names=band_name_list)

    return raster