import os
import numpy as np
from typing import Tuple
from pathlib import Path
from osgeo import gdal

def read_tif(path):

    ext = Path(path).suffix.lower()
    assert ext == '.tif', f'input file must be a tif file, but got {ext}'

    ds = gdal.Open(path)
    return ds

def read_gdal_bands(ds, selected_bands:list[int]=None) -> tuple[list, np.ndarray]:

    if not selected_bands:
        selected_bands = list(range(1, ds.RasterCount + 1))

    assert all([b_idx > 0 for b_idx in selected_bands]), 'selected_bands for gdal should be a list of integer and > 0'

    arr = ds.ReadAsArray(band_list=selected_bands)
    nodata_vals = [ds.GetRasterBand(i).GetNoDataValue() for i in selected_bands]
    nodata_vals = [0 if val is None else val for val in nodata_vals]
    return nodata_vals, arr

def read_gdal_bands_as_dict(ds, all_band_names:list[str], selected_index:list[int]=None) -> Tuple[dict, list[str]]:

    nodata_vals, arr = read_gdal_bands(ds, selected_index)

    if selected_index is None:
        selected_index = list(range(1, ds.RasterCount + 1))

    selected_band_names = [all_band_names[band_index - 1] for band_index in selected_index]

    if arr.ndim == 2:
        arr_dict = { bname : { 'value': arr, 'no_data': no_data } for bname, no_data in zip(selected_band_names, nodata_vals) }
    else:
        arr_dict = { bname : { 'value': arr[i], 'no_data': no_data } for i, (bname, no_data) in enumerate(zip(selected_band_names, nodata_vals)) }

    return arr_dict, selected_band_names

def load_raster_gdal(paths:list[str]) -> list[gdal.Dataset]:

    for path in paths:
        assert os.path.splitext(path)[1] == os.path.splitext(paths[0])[1], f'All input files should have the same extension'
    return [read_tif(path) for path in paths]