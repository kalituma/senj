from typing import Union
from warnings import warn
from core.util import assert_bnames
from core.raster import Raster, RasterType
from core.raster.funcs import check_product_type, get_band_name_and_index
from core.raster.gpf_module import get_band_grid_size_gpf, build_grid_meta_from_gpf
from core.raster.gdal_module import get_band_grid_size_gdal, build_grid_meta_from_gdal

def set_raw_metadict(raster:Raster, raw, meta_dict:dict, selected_bands:list[Union[str, int]]=None):
    raster.raw = raw
    raster.selected_bands = selected_bands
    raster.product_type = check_product_type(meta_dict)
    raster.meta_dict = meta_dict
    return raster

def update_meta_band_map(meta_dict:dict, selected_band:list[Union[str, int]]) -> dict:

    assert 'band_to_index' in meta_dict and 'index_to_band' in meta_dict, 'band_to_index and index_to_band should be in meta_dict'

    new_meta = meta_dict.copy()
    if selected_band is None:
        return new_meta

    assert len(selected_band) > 0, 'selected_band should have at least one band'
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

def get_band_grid_size(raster:Raster, selected_bands:list[str]=None) -> dict:

    if raster.module_type == RasterType.SNAP:
        return get_band_grid_size_gpf(raster.raw, selected_bands=selected_bands)
    elif raster.module_type == RasterType.GDAL:
        _, index = get_band_name_and_index(raster, selected_bands)
        all_band_name = raster.get_band_names()
        return get_band_grid_size_gdal(raster.raw, band_name=all_band_name, selected_index=index)
    else:
        raise NotImplementedError(f'{raster.module_type} is not implemented.')

def build_det_grid(raster:Raster, det_names):
    grids = {}
    for det_name in det_names:
        if raster.module_type == RasterType.SNAP:
            grid_dict = build_grid_meta_from_gpf(raster.raw, det_name)
        elif raster.module_type == RasterType.GDAL:
            grid_dict = build_grid_meta_from_gdal(raster.raw)
        else:
            raise NotImplementedError(f'{raster.module_type} is not implemented')
        grids[f'{int(grid_dict["RESOLUTION"])}'] = grid_dict
    return grids
