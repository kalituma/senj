from core.raster import RasterType
from core.raster.gdal_module import is_bigtiff_gdal
from core.raster.gpf_module import is_bigtiff_gpf

def is_bigtiff(raster_obj):
    if raster_obj.module_type == RasterType.SNAP:
        return is_bigtiff_gpf(raster_obj.raw)
    else:
        return is_bigtiff_gdal(raster_obj.raw)