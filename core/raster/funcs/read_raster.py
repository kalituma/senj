import os
from typing import Union, Tuple, List, AnyStr, Dict, Optional, Any
from pathlib import Path

from core.util import parse_meta_xml, read_pickle, get_btoi_from_tif, dict_to_ordered_list
from core.util.identify import planet_test, identify_product
from core.util.gdal import load_raster_gdal, mosaic_by_file_paths, read_gdal_bands_as_dict
from core.util.snap import load_raster_gpf, mosaic_gpf, rename_bands, read_gpf_bands_as_dict
from core.util.nc import load_raster_nc, read_nc_bands_as_dict

from core.raster import ModuleType, Raster, ProductType
from core.raster.funcs import set_raw_metadict, get_band_name_and_index, create_meta_dict, init_bname_index_in_meta, load_images_paths

def _prepare_paths_and_type(raster: Raster, in_module: ModuleType) -> Tuple[str, ProductType, str]:
    
    raster.module_type = in_module
    
    path = raster.path
    product_type, meta_path = identify_product(path)
    
    if product_type == ProductType.WV and Path(meta_path).suffix.lower() == '.xml':
        path = raster.path = meta_path

    return path, product_type, meta_path

def _load_raw_data(raster: Raster, path: str, product_type: ProductType) -> Tuple[Any, bool]:
   
    image_paths = load_images_paths(path, product_type, raster.module_type)
    update_meta_bounds = False
    
    if raster.module_type == ModuleType.GDAL:
        if len(image_paths) > 1:
            raw = mosaic_by_file_paths(image_paths)
            update_meta_bounds = True
        else:
            if Path(image_paths[0]).suffix.lower() == '.safe':
                raw = load_and_merge_safe(image_paths)
            else:
                datasets = load_raster_gdal(image_paths)
                raw = datasets[0]
            
    elif raster.module_type == ModuleType.SNAP:
        datasets = load_raster_gpf(image_paths)
        if len(datasets) > 1:
            raw = mosaic_gpf(datasets)
            update_meta_bounds = True
        else:
            raw = datasets[0]
            
    elif raster.module_type == ModuleType.NETCDF:
        raws = load_raster_nc(image_paths)
        raw = raws[0]
        
    else:
        raise NotImplementedError(f'Module type({raster.module_type}) is not implemented for the input process.')
        
    return raw, update_meta_bounds

def _prepare_metadata(raw, path: str, product_type: ProductType, module_type: ModuleType, update_meta_bounds: bool) -> Tuple[Dict[str, Any], Dict[str, int]]:
    
    btoi_from_header = None
    if Path(path).suffix[1:].lower() == 'tif':
        btoi_from_header = get_btoi_from_tif(path)
    
    meta_dict = create_meta_dict(raw, product_type, module_type, path, update_meta_bounds=update_meta_bounds)
    meta_dict = init_bname_index_in_meta(meta_dict, raw, product_type=product_type, module_type=module_type, band_to_index=btoi_from_header)
    
    if meta_dict:
        btoi_from_header = None
        
    return meta_dict, btoi_from_header

def apply_band_names_to_snap(raster: Raster, btoi_from_header: Optional[Dict[str, int]], meta_dict: Optional[Dict[str, Any]]) -> Raster:
    
    if raster.module_type != ModuleType.SNAP:
        return raster
        
    if btoi_from_header is not None:
        raster.raw = rename_bands(raster.raw, band_names=dict_to_ordered_list(btoi_from_header))
    elif meta_dict is not None and 'band_to_index' in meta_dict and 'index_to_band' in meta_dict:
        raster.raw = rename_bands(raster.raw, band_names=dict_to_ordered_list(meta_dict['band_to_index']))
        
    return raster

def load_raster(empty_raster: Raster, in_module: ModuleType) -> Raster:
    
    path, product_type, _ = _prepare_paths_and_type(empty_raster, in_module)    
    raw, update_meta_bounds = _load_raw_data(empty_raster, path, product_type)
    meta_dict, btoi_from_header = _prepare_metadata(
        raw, path, product_type, in_module, update_meta_bounds
    )
    empty_raster = set_raw_metadict(empty_raster, raw=raw, meta_dict=meta_dict, product_type=product_type)    
    if meta_dict is None:
        empty_raster = empty_raster.update_index_bnames(btoi_from_header)
    else:
        empty_raster.copy_band_map_from_meta()    
    empty_raster = apply_band_names_to_snap(empty_raster, btoi_from_header, meta_dict)
    
    return empty_raster

def read_band_from_raw(raster:Raster, selected_name_or_id:list[Union[str, int]]=None, add_to_cache=False) -> Raster:

    module_type = raster.module_type

    if selected_name_or_id is None:
        selected_name_or_id = raster.get_band_names()

    bnames, index = get_band_name_and_index(raster, selected_name_or_id)

    if module_type == ModuleType.GDAL:
        all_bnames = raster.get_band_names()
        bands, new_selected_bands = read_gdal_bands_as_dict(raster.raw, all_band_names=all_bnames, selected_index=index)
    elif module_type == ModuleType.SNAP:
        bands, new_selected_bands = read_gpf_bands_as_dict(raster.raw, bnames)
    elif module_type == ModuleType.NETCDF:
        bands, new_selected_bands = read_nc_bands_as_dict(raster.raw, bnames)
    else:
        raise NotImplementedError(f'Module type({module_type}) is not implemented for the input process.')

    if add_to_cache:
        if raster.bands == None:
            raster.bands = bands
            # raster.selected_bands = new_selected_bands
        else:
            raster.bands.update(bands)
            # raster.selected_bands = sorted(set(raster.selected_bands + new_selected_bands))
    else:
        raster.bands = bands
        # raster.selected_bands = new_selected_bands

    raster.is_band_cached = True

    return raster