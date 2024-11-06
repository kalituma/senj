import numpy as np

from typing import TYPE_CHECKING, List
from core.util import load_gdal, load_osr, time_benchmark
from core.util.gdal import create_ds, create_ds_with_arr, RESAMPLING_METHODS

if TYPE_CHECKING:
    from osgeo.gdal import GCP, Dataset

@time_benchmark
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

def reproject_ds_using_gcp(in_ds:"Dataset", gcps:List["GCP"],
                           min_x:float, max_x:float, min_y:float, max_y:float, res:float,
                           resampling_method:str='cubic',
                           in_epsg:int=4326) -> "Dataset":

    gdal = load_gdal()
    osr = load_osr()

    band_num = in_ds.RasterCount

    in_srs = osr.SpatialReference()
    in_srs.ImportFromEPSG(in_epsg)

    in_ds.SetGCPs(gcps, in_srs.ExportToWkt())

    new_width = int((max_x - min_x) / res) + 1
    new_height = int((max_y - min_y) / res) + 1

    dst_srs = osr.SpatialReference()
    dst_srs.ImportFromEPSG(in_epsg)

    dst_ds = create_ds('MEM', new_width, new_height, band_num, 'float32', proj_wkt=dst_srs.ExportToWkt(), transform=(min_x, res, 0, max_y, 0, -res))

    error_threshold = 0.125
    gdal.ReprojectImage(in_ds, dst_ds, None, None, RESAMPLING_METHODS[resampling_method], 0, error_threshold)
    in_ds = None

    return dst_ds

@time_benchmark
def reproject_arr_using_gcp(in_arr:np.ndarray, gcps:List["GCP"],
                            min_x, max_x, min_y, max_y, res:float, resampling_method:str= 'cubic',
                            in_epsg:int=4326, no_data:float=-999.) -> "Dataset":

    osr = load_osr()
    if in_arr.ndim == 2:
        in_arr = in_arr[np.newaxis, :, :]
    elif in_arr.ndim != 3:
        raise ValueError("Input array must be 2D or 3D")

    in_ds = create_ds_with_arr(in_arr, gdal_format='MEM', no_data=no_data)
    out_ds = reproject_ds_using_gcp(in_ds, gcps, min_x, max_x, min_y, max_y, res, resampling_method=resampling_method, in_epsg=in_epsg)

    return out_ds