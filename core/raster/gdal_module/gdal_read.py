import numpy as np
from typing import Tuple
from pathlib import Path
from osgeo import gdal

from core.util import read_pickle

def read_tif(path):

    ext = Path(path).suffix
    assert ext == '.tif', f'input file must be a tif file, but got {ext}'

    ds = gdal.Open(path)
    return ds

def read_gdal_bands(ds, selected_bands:list[int]=None) -> np.ndarray:
    if not selected_bands:
        selected_bands = list(range(1, ds.RasterCount + 1))

    assert all([b_idx > 0 for b_idx in selected_bands]), 'selected_bands for gdal should be a list of integer and > 0'

    arr = ds.ReadAsArray(band_list=selected_bands)

    return arr

def read_gdal_bands_as_dict(ds, selected_bands:list[int]=None) -> Tuple[dict, list[int]]:

    arr = read_gdal_bands(ds, selected_bands)

    if selected_bands is None:
        selected_bands = list(range(1, ds.RasterCount + 1))

    if arr.ndim == 2:
        arr = { b_num : arr for b_num in selected_bands }
    else:
        arr = { b_num : arr[i] for i, b_num in enumerate(selected_bands) }

    return arr, selected_bands

def load_raster_gdal(path, selected_bands:list[int]=None):

    ext = Path(path).suffix
    ds = read_tif(path)

    if selected_bands is None:
        selected_bands = list(range(1, ds.RasterCount + 1))

    meta_path = path.replace(ext, '.pkl')
    if Path(meta_path).exists():
        meta_dict = read_pickle(meta_path)
    else:
        print(f'No meta file is found for {path}')
        meta_dict = {}

    return meta_dict, ds, selected_bands