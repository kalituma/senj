from typing import TYPE_CHECKING, Union, Tuple, Dict, List, Optional, Any

from core.util import ProductType, assert_bnames
from core.util.nc import get_band_names_nc
from core.raster import Raster, ModuleType

if TYPE_CHECKING:
    from osgeo.gdal import Dataset
    from esa_snappy import Product

def check_bname_index_valid(raster: Raster, band_id_list: List[Union[str, int]]) -> bool:
    if band_id_list is None:
        return False

    is_index = all([isinstance(b, int) for b in band_id_list])

    if is_index:
        assert all([b <= raster.get_bands_size() and b > 0 for b in band_id_list]), f'band index should be less than or equal to {raster.get_bands_size()}'
    else:
        assert_bnames(band_id_list, raster.get_band_names(), f'selected bands{band_id_list} should be in source bands({raster.get_band_names()})')

    return True

def get_band_name_and_index(raster: Raster, band_id_list: List[Union[str, int]]) -> Tuple[List[str], List[int]]:
    is_index = all([isinstance(b, int) for b in band_id_list])

    if is_index:
        band_name = raster.index_to_band_name(band_id_list)
        index = band_id_list
    else:
        assert_bnames(band_id_list, raster.get_band_names(), f'selected bands{band_id_list} should be in source bands({raster.get_band_names()})')
        band_name = band_id_list
        index = raster.band_name_to_index(band_id_list)

    return band_name, index

def process_provided_band_to_index(band_to_index: Dict[str, int]) -> Tuple[Dict[str, int], Dict[int, str]]:
    b_to_i = {b: int(i) for b, i in band_to_index.items()}
    i_to_b = {int(i): b for b, i in band_to_index.items()}
    return b_to_i, i_to_b

def process_sentinel_planetscope_capella(raw: Union["Dataset", "Product"], module_type: ModuleType) -> Tuple[Dict[str, int], Dict[int, str]]:
    if module_type == ModuleType.GDAL:
        band_indices = list(range(1, raw.RasterCount + 1))
        bnames = [f'band_{index}' for index in band_indices]
    elif module_type == ModuleType.SNAP:
        bnames = list(raw.getBandNames())
    else:
        raise NotImplementedError(f'{module_type} is not implemented.')
    
    b_to_i = {b: i + 1 for i, b in enumerate(bnames)}
    i_to_b = {i + 1: b for i, b in enumerate(bnames)}
    return b_to_i, i_to_b

def process_worldview(meta_dict: Dict[str, Any]) -> Tuple[Dict[str, int], Dict[int, str]]:
    assert 'BAND_INFO' in meta_dict, f'BAND_INFO is not found in meta_dict'
    b_to_i = {band_name: band_info['index'] for band_name, band_info in meta_dict['BAND_INFO'].items()}
    i_to_b = {band_info['index']: band_name for band_name, band_info in meta_dict['BAND_INFO'].items()}
    return b_to_i, i_to_b

def process_goci_gk2a(raw: Union["Dataset", "Product"], module_type: ModuleType) -> Tuple[Dict[str, int], Dict[int, str]]:
    if module_type == ModuleType.NETCDF:
        band_names = get_band_names_nc(raw)
        b_to_i = {b: i + 1 for i, b in enumerate(band_names)}
        i_to_b = {i + 1: b for i, b in enumerate(band_names)}
        return b_to_i, i_to_b
    
    raise NotImplementedError(f'{module_type} is not implemented for GOCI products.')

def init_bname_index_in_meta(
    meta_dict: Dict[str, Any], 
    raw: Union["Dataset", "Product"], 
    product_type: ProductType, 
    module_type: ModuleType, 
    band_to_index: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    
    if not meta_dict:
        return meta_dict
        
    if 'band_to_index' in meta_dict and 'index_to_band' in meta_dict:
        return meta_dict
    
    try:
        if band_to_index:
            b_to_i, i_to_b = process_provided_band_to_index(band_to_index)
        
        elif product_type in [ProductType.S1, ProductType.S2, ProductType.PS, ProductType.CP]:
            b_to_i, i_to_b = process_sentinel_planetscope_capella(raw, module_type)
            
        elif product_type == ProductType.WV:
            b_to_i, i_to_b = process_worldview(meta_dict)
            
        elif product_type in [ProductType.GOCI_CDOM, ProductType.GOCI_AC]:
            b_to_i, i_to_b = process_goci_gk2a(raw, module_type)
            
        else:
            raise NotImplementedError(f'{product_type} is not implemented.')
            
        meta_dict['band_to_index'] = b_to_i
        meta_dict['index_to_band'] = i_to_b
        
    except Exception as e:
        print(f"Error initializing band name index: {e}")
    
    return meta_dict