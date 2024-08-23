from core.raster import RasterType
from core.util.gdal import projection_tif_gdal
from core.util.snap import projection_tif_snap

def load_proj_from_raw(raw, module_type:RasterType):

    if module_type == RasterType.GDAL:
        return projection_tif_gdal(raw)
    elif module_type == RasterType.SNAP:
        return projection_tif_snap(raw)