from typing import Union
from pathlib import Path
from core.util import assert_bnames
from core.raster import RasterType, Raster, raster_type
from core.raster.gpf_module import find_proj_from_band, create_product, add_band_to_product, find_gt_from_band, copy_product
from core.raster.gdal_module import create_ds_with_dict, copy_ds
from core.raster.funcs import read_band_from_raw, set_raw_metadict, update_meta_band_map

def wrap_up_raster(raster_obj:Raster, selected_bands:list[str], out_module:Union[RasterType, str]) -> Raster:

    if selected_bands is not None:
        src_bands = raster_obj.get_band_names()
        assert_bnames(selected_bands, src_bands, f'selected bands{selected_bands} should be in source bands({src_bands})')

    previous_module_type = raster_obj.module_type
    out_module_type = raster_type(out_module)

    if previous_module_type == out_module_type:
        if out_module_type == RasterType.SNAP:
            raw = copy_product(raster_obj.raw, selected_bands)
        elif out_module_type == RasterType.GDAL:
            if selected_bands:
                selected_index = raster_obj.band_names_to_indices(selected_bands)
            else:
                selected_index = None
            raw = copy_ds(raster_obj.raw, 'MEM', selected_index=selected_index)
        else:
            raise NotImplementedError(f'Raster type {out_module_type.__str__()} is not implemented')

        update_meta_band_map(raster_obj.meta_dict, selected_bands)
        raster_obj = set_raw_metadict(raster_obj, raw=raw, meta_dict=raster_obj.meta_dict,selected_bands=selected_bands)
    else:
        raster_obj = convert_raster_func(raster_obj, out_module_type)
    raster_obj.del_bands_cache()

    return raster_obj

def convert_raster_func(raster_obj:Raster, out_module_type:RasterType) -> Raster:
    assert raster_obj.module_type != out_module_type, 'input and output module type should be different'
    # cached to raw
    if not raster_obj.is_band_cached:
        raster_obj = read_band_from_raw(raster_obj, raster_obj.selected_bands)

    if out_module_type == RasterType.SNAP:
        raster_obj = convert_to_gpf(raster_obj) # Product
    elif out_module_type == RasterType.GDAL:
        raster_obj = convert_to_gdal(raster_obj) # MEM dataset
    else:
        raise NotImplementedError(f'Raster type {out_module_type.__str__()} is not implemented')

    return raster_obj

def convert_to_gpf(raster_obj:Raster) -> Raster:

    if raster_obj.module_type == RasterType.GDAL:
        product_name = Path(raster_obj.path).stem
        width, height = raster_obj.raw.RasterXSize, raster_obj.raw.RasterYSize
        product = create_product(product_name, file_format='dim', width=width, height=height)
        selected_bands = {bname: raster_obj.bands[bname] for bname in raster_obj.selected_bands}
        product = add_band_to_product(product, selected_bands)
        raster_obj.raw = product
    else:
        raise NotImplementedError('another type to SNAP is not implemented')

    return raster_obj

def convert_to_gdal(raster_obj:Raster) -> Raster:

    assert raster_obj.is_band_cached, 'bands should be loaded in the cache before converting to GDAL'

    if raster_obj.module_type == RasterType.SNAP:
        wkt = find_proj_from_band(raster_obj.raw.getBand(raster_obj.selected_bands[0]))
        gt = find_gt_from_band(raster_obj.raw.getBand(raster_obj.selected_bands[0]))
        raster_obj.bands = {i+1 : value for i, (key, value) in enumerate(raster_obj.bands.items()) if key in raster_obj.selected_bands}
        raster_obj.selected_bands = list(raster_obj.bands.keys())
    else:
        raise NotImplementedError('another type to GDAL is not implemented')

    raster_obj.raw = create_ds_with_dict(raster_obj.bands, 'MEM', proj_wkt=wkt, transform=gt, metadata=None, selected_bands=raster_obj.selected_bands, out_path='')
    raster_obj.module_type = RasterType.GDAL

    return raster_obj


