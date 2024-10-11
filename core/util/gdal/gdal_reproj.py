import numpy as np

from typing import TYPE_CHECKING, List
from core.util import load_gdal, load_osr
from core.util.gdal import create_ds

if TYPE_CHECKING:
    from osgeo.gdal import GCP, Dataset

def create_gcp(lons:np.ndarray, lats:np.ndarray, grid_size:int=20) -> List["GCP"]:

    gdal = load_gdal()

    gcps = []
    rows, cols = lons.shape
    for row in range(0, rows, grid_size):
        for col in range(0, cols, grid_size):
            x = float(lons[row, col])
            y = float(lats[row, col])
            gcp = gdal.GCP(x, y, 0, col, row)
            gcps.append(gcp)
    return gcps

def reproject_ds_using_gcp(in_ds:"Dataset", gcps:List["GCP"], min_x, min_y, max_x, max_y, res:float, in_epsg:int=4326) -> "Dataset":

    gdal = load_gdal()
    osr = load_osr()

    band_num = in_ds.RasterCount

    src_srs = osr.SpatialReference()
    src_srs.ImportFromEPSG(in_epsg)
    in_ds.SetGCPs(gcps, src_srs.ExportToWkt())

    new_width = int((max_x - min_x) / res) + 1
    new_height = int((max_y - min_y) / res) + 1

    dst_srs = osr.SpatialReference()
    dst_srs.ImportFromEPSG(in_epsg)

    dst_ds = create_ds('MEM', new_width, new_height, band_num, 'float32', dst_srs.ExportToWkt(), (min_x, res, 0, max_y, 0, -res))

