from typing import Union
from osgeo.gdal import Dataset
from esa_snappy import Product

from core.raster import RasterType
from core.util import ProductType

def create_band_name_idx(meta_dict:dict, raw:Union[Dataset, Product], product_type:ProductType, module_type:RasterType) -> dict:

    if 'band_to_index' not in meta_dict or 'index_to_band' not in meta_dict:
        if product_type == ProductType.S1 or product_type == ProductType.S2:
            if module_type == RasterType.GDAL:
                band_indices = list(range(1, raw.RasterCount + 1))
                bnames = [f'band_{index}' for index in band_indices]
            elif module_type == RasterType.SNAP:
                bnames = list(raw.getBandNames())
            else:
                raise NotImplementedError(f'{module_type} is not implemented.')
            meta_dict['band_to_index'] = {b: i + 1 for i, b in enumerate(bnames)}
            meta_dict['index_to_band'] = {i + 1: b for i, b in enumerate(bnames)}

        if product_type == ProductType.WV:
            assert 'BAND_INFO' in meta_dict, f'BAND_INFO is not found in meta_dict'
            meta_dict['band_to_index'] = {band_name:band_info['index'] for band_name, band_info in meta_dict['BAND_INFO'].items()}
            meta_dict['index_to_band'] = {band_info['index']:band_name for band_name, band_info in meta_dict['BAND_INFO'].items()}

        if product_type == ProductType.PS:
            pass

    return meta_dict