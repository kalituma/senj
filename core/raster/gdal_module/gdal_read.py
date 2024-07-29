import numpy as np
from typing import Tuple
from pathlib import Path
from osgeo import gdal

from core.util import read_pickle, assert_bnames

def read_tif(path):

    ext = Path(path).suffix
    assert ext == '.tif', f'input file must be a tif file, but got {ext}'

    ds = gdal.Open(path)
    return ds

def read_gdal_bands(ds, selected_bands:list[int]=None) -> tuple[list, np.ndarray]:
    if not selected_bands:
        selected_bands = list(range(1, ds.RasterCount + 1))

    assert all([b_idx > 0 for b_idx in selected_bands]), 'selected_bands for gdal should be a list of integer and > 0'

    arr = ds.ReadAsArray(band_list=selected_bands)
    nodata_vals = [ds.GetRasterBand(i).GetNoDataValue() for i in selected_bands]
    return nodata_vals, arr

def read_gdal_bands_as_dict(ds, selected_bands:list[int]=None, band_name_map:dict=None) -> Tuple[dict, list[int]]:

    nodata_vals, arr = read_gdal_bands(ds, selected_bands)

    if selected_bands is None:
        selected_bands = list(range(1, ds.RasterCount + 1))



    if arr.ndim == 2:
        arr_dict = { b_num : { 'value': arr, 'no_data': no_data } for b_num, no_data in zip(selected_bands, nodata_vals) }
    else:
        arr_dict = { b_num : { 'value': arr[i], 'no_data': no_data } for i, (b_num, no_data) in enumerate(zip(selected_bands, nodata_vals)) }

    return arr_dict, selected_bands

def load_raster_gdal(path, selected_bands:list[int]=None):

    ext = Path(path).suffix
    ds = read_tif(path)

    band_range = list(range(1, ds.RasterCount + 1))

    if selected_bands:
        assert_bnames(selected_bands, band_range, f'selected bands {selected_bands} is not found in {band_range}')

    meta_path = path.replace(ext, '.pkl')
    if Path(meta_path).exists():
        meta_dict = read_pickle(meta_path)
    else:
        print(f'No meta file is found for {path}')
        meta_dict = None

    return meta_dict, ds, selected_bands