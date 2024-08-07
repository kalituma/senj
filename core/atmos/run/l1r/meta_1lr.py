
from core.raster import Raster

from core.raster.gpf_module import find_grids_and_angle_meta, get_product_info_meta, get_band_info_meta, get_granule_info, get_src_param, warp_to
from core.raster.funcs import get_band_grid_size

def meta_dict_to_l1r_meta(raster: "Raster", selected_band:list[str]=None) -> dict:

    assert raster.meta_dict, 'Raster meta data is not available.'

    meta_dict = raster.meta_dict

    granule_info = get_granule_info(meta_dict)

    granule_meta = find_grids_and_angle_meta(meta_dict) # Sun, View

    granule_meta['granule_info'] = granule_info
    size_meta_per_band = get_band_grid_size(raster, selected_band)

    product_info = get_product_info_meta(meta_dict) # Time, Spacecraft, Orbit
    sensor_response = get_band_info_meta(meta_dict) # Wavelength, RSR

    return {
        'granule_meta': granule_meta,
        'size_meta_per_band': size_meta_per_band,
        'product_info': product_info,
        'sensor_response': sensor_response
    }