from typing import Union
from core.util import identify_product
from core.raster import RasterType, Raster
from core.raster.gdal_module import load_raster_gdal
from core.raster.gpf_module import load_raster_gpf
from core.raster.funcs import read_gdal_bands_as_dict, read_gpf_bands_as_dict, set_raw_metadict, get_band_name_and_index, create_meta_dict


def load_raster(raster:Raster, in_module:RasterType, selected_bands:list[Union[str, int]]=None, bname_word_included:bool=False):

    path = raster.path
    raster.module_type = in_module

    if bname_word_included:
        assert in_module == RasterType.SNAP, 'bname_word_included is only available for SNAP module'

    product_type = identify_product(path)

    if raster.module_type == RasterType.GDAL:
        if selected_bands:
            assert all([isinstance(b, int) for b in selected_bands]), f'selected_bands for module "{RasterType.GDAL.__str__()}" should be a list of integer'
            assert all([b > 0 for b in selected_bands]), f'selected_bands for module "{RasterType.GDAL.__str__()}" should be > 0'
        raw, new_selected_bands = load_raster_gdal(path, selected_bands=selected_bands)
    elif raster.module_type == RasterType.SNAP:
        if selected_bands:
            if all([isinstance(b, int) for b in selected_bands]):
                selected_bands = [str(f'band_{b}') for b in selected_bands]
        raw, new_selected_bands = load_raster_gpf(path, selected_bands, bname_word_included)
    else:
        raise NotImplementedError(f'Module type({in_module}) is not implemented for the input process.')

    meta_dict = create_meta_dict(raw, product_type, path)

    if selected_bands:
        raster = set_raw_metadict(raster, raw=raw, meta_dict=meta_dict, product_type=product_type, selected_bands=new_selected_bands)
    else:
        raster = set_raw_metadict(raster, raw=raw, meta_dict=meta_dict, product_type=product_type)

    return raster

def read_band_from_raw(raster:Raster, selected_band:list[Union[str, int]]=None) -> Raster:

    module_type = raster.module_type

    if module_type == RasterType.GDAL:
        _, index = get_band_name_and_index(raster, selected_band)
        raster.bands, raster.selected_bands = read_gdal_bands_as_dict(raster.raw, band_names=raster.get_band_names(), selected_index=index)
    elif module_type == RasterType.SNAP:
        raster.bands, raster.selected_bands = read_gpf_bands_as_dict(raster.raw, selected_band)
    else:
        raise NotImplementedError(f'Module type({module_type}) is not implemented for the input process.')

    raster.is_band_cached = True

    return raster