from core.raster import Raster, ModuleType
from core.util.gdal import mosaic_by_ds
from core.util.snap import mosaic_gpf
from core.raster.funcs.meta import MetaBandsManager

def mosaic_raster_func(rasters:list[Raster], module_type:ModuleType):

    raw_list = [r.raw for r in rasters]

    band_name_list = rasters[0].get_band_names()
    if module_type == ModuleType.GDAL:
        mosaic_raw = mosaic_by_ds(raw_list)
    elif module_type == ModuleType.SNAP:
        mosaic_raw = mosaic_gpf(raw_list)
        band_name_list = list(mosaic_raw.getBandNames())
    else:
        raise NotImplementedError(f'Raster type {rasters[0].module_type} is not implemented')

    new_product_type = rasters[0].product_type
    mosaic_raster = Raster.from_raster(rasters[0], path='', raw=mosaic_raw, module_type=module_type, product_type=new_product_type)
    MetaBandsManager(mosaic_raster).update_band_mapping(band_name_list)

    return mosaic_raster