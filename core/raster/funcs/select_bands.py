from typing import List, Union
from core.util import assert_bnames, glob_match, ModuleType
from core.raster import Raster

from core.util.snap import copy_product
from core.util.gdal import copy_ds
from core.util.nc import copy_nc_ds
from core.raster.funcs.meta import MetaDictManager
from core.raster.funcs import get_band_name_and_index


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

    # new_raster = Raster.from_raster(raster)

    if raster.module_type == ModuleType.GDAL:
        assert all([b > 0 for b in selected_index]), f'selected_bands for module "{ModuleType.GDAL.__str__()}" should be > 0'
        raw = copy_ds(raster.raw, 'MEM', selected_index=selected_index)
    elif raster.module_type == ModuleType.SNAP:
        raw = copy_product(raster.raw, selected_bands=selected_band_name, copy_tie_point=False)
    elif raster.module_type == ModuleType.NETCDF:
        raw = copy_nc_ds(raster.raw, selected_bands=selected_band_name)
    else:
        raise NotImplementedError(f'Raster type {raster.module_type.__str__()} is not implemented')

    new_band_name = _update_duplicated_band_names(selected_band_name)
    raster.raw = raw
    if raster.meta_dict:
        MetaDictManager(raster).update_band_mapping(new_band_name)

    # new_raster = set_raw_metadict(new_raster, raw, raster.product_type, new_meta)
    # new_raster = new_raster.update_index_bnames(bnames=new_band_name)

    return raster

def _update_duplicated_band_names(selected_band_name:List[str]) -> List[str]:
    # if duplicated band names in selected_band_name, update selected_band_name to unique band names
    if len(selected_band_name) != len(set(selected_band_name)):
        count_book = {b:0 for b in set(selected_band_name)}

        acc_mask = []
        for b in selected_band_name:
            if selected_band_name.count(b) > 1:
                count_book[b]+=1            
            else:
                count_book[b]=1
            acc_mask.append(count_book[b])

        # rename duplicated band names
        new_band_name = [f'{b}_{acc_mask[i]}' if acc_mask[i] > 1 else b for i, b in enumerate(selected_band_name)]
    else:
        new_band_name = selected_band_name

    return new_band_name