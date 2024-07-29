from typing import Union
from warnings import warn
from core.util import assert_bnames
from core.raster import Raster, RasterType
from core.raster.funcs import check_product_type

def set_raw_metadict(raster:Raster, raw, meta_dict:dict, selected_bands:list[Union[str, int]]=None):
    raster.raw = raw
    raster.selected_bands = selected_bands
    raster.product_type = check_product_type(meta_dict)
    raster.meta_dict = meta_dict
    return raster

def update_meta_band_map(meta_dict:dict, selected_band:list[Union[str, int]]) -> dict:

    assert 'band_to_index' in meta_dict and 'index_to_band' in meta_dict, 'band_to_index and index_to_band should be in meta_dict'

    assert len(selected_band) > 0, 'selected_band should have at least one band'

    new_meta = meta_dict.copy()

    is_index = all([isinstance(b, int) for b in selected_band])

    if is_index:
        src_index = list(meta_dict['index_to_band'].keys())
        assert_bnames(selected_band, list(meta_dict['index_to_band'].keys()), f'selected index {selected_band} should be in index_to_band {src_index}')
    else:
        src_band = list(meta_dict['index_to_band'].values())
        assert_bnames(selected_band, list(meta_dict['index_to_band'].values()), f'selected bands {selected_band} should be in index_to_band {src_band}')

    if is_index:
        new_meta['band_to_index'] = {new_meta['index_to_band'][idx]: new_idx+1 for new_idx, idx in enumerate(selected_band)}
        new_meta['index_to_band'] = {new_idx+1: new_meta['index_to_band'][idx] for new_idx, idx in enumerate(selected_band)}
    else:
        new_meta['band_to_index'] = {b: i+1 for i, b in enumerate(selected_band)}
        new_meta['index_to_band'] = {i+1: b for i, b in enumerate(selected_band)}

    return new_meta