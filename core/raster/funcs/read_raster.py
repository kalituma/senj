from typing import Union
from core.raster import RasterType, Raster

from core.raster.gdal_module import load_raster_gdal
from core.raster.gpf_module import load_raster_gpf
from core.raster.funcs import read_gdal_bands_as_dict, read_gpf_bands_as_dict, check_product_type


def load_raster(raster:Raster, in_module:RasterType, selected_bands:list[Union[str, int]]=None, bname_word_included:bool=False):

    path = raster.path
    raster.module_type = in_module


    if raster.module_type == RasterType.GDAL:
        if selected_bands:
            assert [isinstance(b, int) for b in selected_bands], f'selected_bands for {RasterType.SNAP} should be a list of integer'
            assert all([b > 0 for b in selected_bands]), f'selected_bands for {RasterType.SNAP} should be > 0'
        meta_dict, raw, new_selected_bands = load_raster_gdal(path, selected_bands=selected_bands)
    elif raster.module_type == RasterType.SNAP:
        if selected_bands:
            assert [isinstance(b, str) for b in selected_bands], f'selected_bands for {RasterType.SNAP} should be a list of string'
        meta_dict, raw, new_selected_bands = load_raster_gpf(path, selected_bands, bname_word_included)
    else:
        raise NotImplementedError(f'Module type({in_module}) is not implemented for the input process.')

    if selected_bands:
        raster.selected_bands = new_selected_bands
    raster.meta_dict = meta_dict
    raster.raw = raw
    raster.product_type = check_product_type(meta_dict)
    return raster

def read_band_from_raw(raster:Raster, selected_band:list[Union[str, int]]) -> Raster:

    module_type = raster.module_type

    if module_type == RasterType.GDAL:
        raster.bands, raster.selected_bands = read_gdal_bands_as_dict(raster.raw, selected_band)
    elif module_type == RasterType.SNAP:
        raster.bands, raster.selected_bands = read_gpf_bands_as_dict(raster.raw, selected_band)
    else:
        raise NotImplementedError(f'Module type({module_type}) is not implemented for the input process.')

    raster.is_band_cached = True

    return raster