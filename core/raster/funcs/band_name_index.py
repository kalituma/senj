from typing import Union

from core.raster import Raster

def get_band_name_and_index(raster:Raster, band_id_list:list[Union[str, int]]) -> tuple[list[str], list[int]]:

    if band_id_list is None:
        band_id_list = raster.get_band_names()

    is_index = all([isinstance(b, int) for b in band_id_list])

    if is_index:
        band_name = raster.index_to_band_name(band_id_list)
        index = band_id_list
    else:
        band_name = band_id_list
        index = raster.band_name_to_index(band_id_list)

    return band_name, index