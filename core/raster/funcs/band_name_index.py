from typing import TYPE_CHECKING, Union, Tuple

from core.util import ProductType, assert_bnames, get_btoi_from_tif
from core.util.nc import get_band_names_nc
from core.raster import Raster, ModuleType

if TYPE_CHECKING:
    from osgeo.gdal import Dataset
    from esa_snappy import Product

def check_bname_index_valid(raster:Raster, band_id_list:list[Union[str, int]]) -> bool:

    if band_id_list is None:
        return False

    is_index = all([isinstance(b, int) for b in band_id_list])

    if is_index:
        assert all([b <= raster.get_bands_size() and b > 0 for b in band_id_list]), f'band index should be less than or equal to {raster.get_bands_size()}'
    else:
        assert_bnames(band_id_list, raster.get_band_names(), f'selected bands{band_id_list} should be in source bands({raster.get_band_names()})')

    return True

def get_band_name_and_index(raster:Raster, band_id_list:list[Union[str, int]]) -> tuple[list[str], list[int]]:

    is_index = all([isinstance(b, int) for b in band_id_list])

    if is_index:
        band_name = raster.index_to_band_name(band_id_list)
        index = band_id_list
    else:
        assert_bnames(band_id_list, raster.get_band_names(), f'selected bands{band_id_list} should be in source bands({raster.get_band_names()})')
        band_name = band_id_list
        index = raster.band_name_to_index(band_id_list)

    return band_name, index

def init_bname_index_in_meta(meta_dict:dict, raw:Union["Dataset", "Product"], product_type:ProductType, module_type:ModuleType, band_to_index:dict=None) -> dict:

    if meta_dict:
        if 'band_to_index' not in meta_dict or 'index_to_band' not in meta_dict:
            if band_to_index:
                meta_dict['band_to_index'] = {b: int(i) for b, i in band_to_index.items()}
                meta_dict['index_to_band'] = {int(i): b for b, i in band_to_index.items()}
            else:
                if product_type == ProductType.S1 or product_type == ProductType.S2 or product_type == ProductType.PS:
                    if module_type == ModuleType.GDAL:
                        band_indices = list(range(1, raw.RasterCount + 1))
                        bnames = [f'band_{index}' for index in band_indices]
                    elif module_type == ModuleType.SNAP:
                        bnames = list(raw.getBandNames())
                    else:
                        raise NotImplementedError(f'{module_type} is not implemented.')
                    meta_dict['band_to_index'] = {b: i + 1 for i, b in enumerate(bnames)}
                    meta_dict['index_to_band'] = {i + 1: b for i, b in enumerate(bnames)}
                elif product_type == ProductType.WV:
                    assert 'BAND_INFO' in meta_dict, f'BAND_INFO is not found in meta_dict'
                    meta_dict['band_to_index'] = {band_name:band_info['index'] for band_name, band_info in meta_dict['BAND_INFO'].items()}
                    meta_dict['index_to_band'] = {band_info['index']:band_name for band_name, band_info in meta_dict['BAND_INFO'].items()}
                elif product_type == ProductType.GOCI_CDOM or product_type == ProductType.GOCI_AC:
                    if module_type == ModuleType.NETCDF:
                        meta_dict['band_to_index'] = {b:i+1 for i, b in enumerate(get_band_names_nc(raw))}
                        meta_dict['index_to_band'] = {i+1:b for i, b in enumerate(get_band_names_nc(raw))}

                else:
                    raise NotImplementedError(f'{product_type} is not implemented.')


    return meta_dict