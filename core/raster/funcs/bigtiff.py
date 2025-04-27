from core.raster import ModuleType
from core.util.asserts import deprecated
from core.util.gdal import is_bigtiff_gdal
from core.util.snap import is_bigtiff_gpf

@deprecated
def is_bigtiff(raster_obj): #done
    if raster_obj.module_type == ModuleType.SNAP:
        return is_bigtiff_gpf(raster_obj.raw)
    else:
        return is_bigtiff_gdal(raster_obj.raw)