from core.raster import ModuleType
from core.util.gdal import projection_tif_gdal
from core.util.snap import projection_tif_snap

def load_proj_from_raw(raw, module_type:ModuleType):

    if module_type == ModuleType.GDAL:
        return projection_tif_gdal(raw)
    elif module_type == ModuleType.SNAP:
        return projection_tif_snap(raw)