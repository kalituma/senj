from typing import Union
from core.raster import RasterType, Raster, ProductType

from core.raster.gdal_module import load_raster_gdal
from core.raster.gpf_module import load_raster_gpf
from core.raster.funcs import read_gdal_bands_as_dict, read_gpf_bands_as_dict, set_raw_metadict


def load_raster(raster:Raster, in_module:RasterType, selected_bands:list[Union[str, int]]=None, bname_word_included:bool=False):

    path = raster.path
    raster.module_type = in_module

    if bname_word_included:
        assert in_module == RasterType.SNAP, 'bname_word_included is only available for SNAP module'

    if raster.module_type == RasterType.GDAL:
        if selected_bands:
            assert all([isinstance(b, int) for b in selected_bands]), f'selected_bands for module "{RasterType.GDAL.__str__()}" should be a list of integer'
            assert all([b > 0 for b in selected_bands]), f'selected_bands for module "{RasterType.GDAL.__str__()}" should be > 0'
        meta_dict, raw, new_selected_bands = load_raster_gdal(path, selected_bands=selected_bands)
    elif raster.module_type == RasterType.SNAP:
        if selected_bands:
            if all([isinstance(b, int) for b in selected_bands]):
                selected_bands = [str(f'band_{b}') for b in selected_bands]

        meta_dict, raw, new_selected_bands = load_raster_gpf(path, selected_bands, bname_word_included)
    else:
        raise NotImplementedError(f'Module type({in_module}) is not implemented for the input process.')

    if selected_bands:
        raster = set_raw_metadict(raster, raw=raw, meta_dict=meta_dict, selected_bands=new_selected_bands)
    else:
        raster = set_raw_metadict(raster, raw=raw, meta_dict=meta_dict)

    return raster

def read_band_from_raw(raster:Raster, selected_band:list[Union[str, int]]=None, band_name_map:dict=None) -> Raster:

    module_type = raster.module_type

    if module_type == RasterType.GDAL:
        raster.bands, raster.selected_bands = read_gdal_bands_as_dict(raster.raw, selected_band, band_name_map)
    elif module_type == RasterType.SNAP:
        raster.bands, raster.selected_bands = read_gpf_bands_as_dict(raster.raw, selected_band)
    else:
        raise NotImplementedError(f'Module type({module_type}) is not implemented for the input process.')

    raster.is_band_cached = True

    return raster