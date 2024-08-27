from core.raster import RasterType, Raster
from core.util import wkt_to_epsg
from core.util.snap import find_epsg_from_product, find_gt_from_product

def get_epsg(raster:Raster):
    if raster.module_type == RasterType.SNAP:
        return find_epsg_from_product(raster.raw)
    else:
        return wkt_to_epsg(raster.raw.GetProjection())

def get_res(raster:Raster):
    if raster.module_type == RasterType.SNAP:
        gt = find_gt_from_product(raster.raw)
        return gt[1]
    else:
        return raster.raw.GetGeoTransform()[1]