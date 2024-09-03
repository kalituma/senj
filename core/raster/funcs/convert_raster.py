from typing import Union
from pathlib import Path
from core.util import assert_bnames

from core.raster import RasterType, Raster, raster_type
from core.util.snap import find_proj_from_band, create_product, add_band_to_product, find_gt_from_band, copy_product, find_geocoding_from_wkt
from core.util.gdal import create_ds_with_dict, copy_ds
from core.raster.funcs import read_band_from_raw, set_raw_metadict, update_meta_band_map, get_band_name_and_index

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
            band_name, index = get_band_name_and_index(raster_obj, selected_bands)
            raw = copy_ds(raster_obj.raw, 'MEM', selected_index=index)
        else:
            raise NotImplementedError(f'Raster type {out_module_type.__str__()} is not implemented')

        if raster_obj.meta_dict:
            new_meta = update_meta_band_map(raster_obj.meta_dict, selected_bands)
        else:
            new_meta = None

        raster_obj = set_raw_metadict(raster_obj, raw=raw, meta_dict=new_meta, selected_bands=selected_bands, product_type=raster_obj.product_type)
        raster_obj = raster_obj.update_index_bnames()
    else:
        raster_obj = convert_raster(raster_obj, out_module_type)

    raster_obj.del_bands_cache()

    return raster_obj

def convert_raster(raster_obj:Raster, out_module:RasterType) -> Raster:
    assert raster_obj.module_type != out_module, 'input and output module type should be different'

    # bands should be loaded before converting
    if not raster_obj.is_band_cached:
        raster_obj = read_band_from_raw(raster_obj, selected_name_or_id=None)

    if out_module == RasterType.SNAP:
        raster_obj = _convert_to_gpf(raster_obj, cached_bands=raster_obj.bands) # Product
    elif out_module == RasterType.GDAL:
        raster_obj = _convert_to_gdal(raster_obj, cache_bands=raster_obj.bands) # MEM dataset
    else:
        raise NotImplementedError(f'Raster type {out_module.__str__()} is not implemented')

    raster_obj.del_bands_cache()

    return raster_obj

def _convert_to_gpf(target_raster:Raster, cached_bands:dict) -> Raster:

    if target_raster.module_type == RasterType.GDAL:
        product_name = Path(target_raster.path).stem
        width, height = target_raster.raw.RasterXSize, target_raster.raw.RasterYSize
        product = create_product(product_name, file_format='dim', width=width, height=height)
        geocoding = find_geocoding_from_wkt(target_raster.raw.GetProjection(), target_raster.raw.GetGeoTransform(),
                                            target_raster.raw.RasterXSize, target_raster.raw.RasterYSize)
        product.setSceneGeoCoding(geocoding)
        product = add_band_to_product(product, cached_bands)
        target_raster.raw = product
    else:
        raise NotImplementedError('another type to SNAP is not implemented')

    return target_raster

def _convert_to_gdal(target_obj:Raster, cache_bands:dict) -> Raster:

    assert target_obj.is_band_cached, 'bands should be loaded in the cache before converting to GDAL'

    band_name_list = list(cache_bands.keys())

    if target_obj.module_type == RasterType.SNAP:
        wkt = find_proj_from_band(target_obj.raw.getBand(band_name_list[0]))
        gt = find_gt_from_band(target_obj.raw.getBand(band_name_list[0]))
        target_obj.raw = create_ds_with_dict(cache_bands, gdal_format='MEM', proj_wkt=wkt, transform=gt, metadata=None, out_path='')
    else:
        raise NotImplementedError('another type to GDAL is not implemented')

    return target_obj


