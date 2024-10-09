from typing import List, Union
from core.util import assert_bnames, glob_match, ModuleType
from core.raster import Raster

from core.util.snap import copy_product
from core.util.gdal import copy_ds
from core.raster.funcs import set_raw_metadict, update_meta_band_map, get_band_name_and_index


def find_bands_contains_word(raster:Raster, bname_word):
    src_bands = raster.get_band_names()
    selected_bands = glob_match(src_bands, bname_word)
    if len(selected_bands) == 0:
        selected_bands = None
    return selected_bands

def select_band_raster(raster:Raster, selected_bands_or_indices:List[Union[int,str]]) -> Raster:

    src_bands = raster.get_band_names()
    selected_band_name, selected_index = get_band_name_and_index(raster, selected_bands_or_indices)
    assert_bnames(selected_band_name, src_bands, f'bands list to split {selected_band_name} should be in source bands({src_bands})')

    new_raster = Raster.from_raster(raster)

    if raster.module_type == ModuleType.GDAL:
        assert all([b > 0 for b in selected_index]), f'selected_bands for module "{ModuleType.GDAL.__str__()}" should be > 0'
        raw = copy_ds(raster.raw, 'MEM', selected_index=selected_index)
    elif raster.module_type == ModuleType.SNAP:
        raw = copy_product(raster.raw, selected_bands=selected_band_name, copy_tie_point=False)
    else:
        raise NotImplementedError(f'Raster type {raster.module_type.__str__()} is not implemented')

    if raster.meta_dict:
        new_meta = update_meta_band_map(raster.meta_dict, selected_band_name)
    else:
        new_meta = None

    new_raster = set_raw_metadict(new_raster, raw, raster.product_type, new_meta)
    new_raster = new_raster.update_index_bnames(bnames=selected_band_name)

    return new_raster