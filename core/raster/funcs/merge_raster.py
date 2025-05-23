from typing import Union

from core.raster import Raster, ModuleType
from core.util import assert_bnames, ProductType
from core.util.snap import merge as merge_gpf
from core.util.gdal import merge as merge_gdal
from core.raster.funcs.meta import MetaBandsManager
def merge_product_types(rasters:list[Raster]):
    product_types = [r.product_type for r in rasters]
    if len(set(product_types)) > 1:
        return ProductType.UNKNOWN
    return product_types[0]

def merge_raster_func(rasters:list[Raster], module_type:ModuleType, geo_err:float):

    raw_list = [r.raw for r in rasters]

    band_name_list = []
    if module_type == ModuleType.GDAL:
        merged = merge_gdal(raw_list)
        for i, r in enumerate(rasters):
            if i == 0:
                ds_name = 'masterDs'
            else:
                ds_name = f'slaveDs{i}'
            band_name_list += [f'{ds_name}${b}' for b in r.get_band_names()]
    elif module_type == ModuleType.SNAP:
        merged = merge_gpf(raw_list, geo_err)
        band_name_list = list(merged.getBandNames())
    else:
        raise NotImplementedError(f'Raster type {rasters[0].module_type} is not implemented')

    new_product_type = merge_product_types(rasters)
    merged_raster = Raster.from_raster(rasters[0], path='', raw=merged, module_type=module_type, product_type=new_product_type)

    MetaBandsManager(merged_raster).update_band_mapping(band_name_list)

    return merged_raster