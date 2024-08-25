from core.raster import RasterType, Raster
from core.util import wkt_to_epsg
from core.util.snap import find_epsg_from_product

def get_epsg(raster:Raster):
    if raster.module_type == RasterType.SNAP:
        return find_epsg_from_product(raster.raw)
    else:
        return wkt_to_epsg(raster.raw.GetProjection())
