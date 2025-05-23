import os
from pathlib import Path
import numpy as np
from typing import Union, TYPE_CHECKING

from osgeo_utils.gdal_merge import names_to_fileinfos
from osgeo import gdal

from core.util import assert_ds_equal
from core.util.gdal import read_gdal_bands, create_ds_with_arr, file_info

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

def get_merged_len_gdal(datasets: list["Dataset"], sbands: Union[list[Union[list[int], None]], None], cobands: Union[list[list[int]], None]):
    len_sum = 0
    for product, sband, cband in zip(datasets, sbands, cobands):
        if cband:
            selected_bands = cband
        elif sband:
            selected_bands = sband
        else:
            selected_bands = list(range(1, product.RasterCount + 1))
        len_sum += len(selected_bands)

    return len_sum

def merge(datasets:list["Dataset"]):

    assert_ds_equal(datasets)

    band_list = []
    no_data_list = []
    for ds in datasets:
        no_data, band_arr = read_gdal_bands(ds)
        if band_arr.ndim != 3:
            band_arr = band_arr[np.newaxis, :, :]
        band_list.append(band_arr)
        no_data_list += no_data
    concat_band = np.concatenate(band_list, axis=0)

    merged_ds = create_ds_with_arr(concat_band, gdal_format='MEM', proj_wkt=datasets[0].GetProjection(), transform=datasets[0].GetGeoTransform(),
                                   no_data=no_data_list[0])

    for i in range(0, merged_ds.RasterCount):
        merged_ds.GetRasterBand(i + 1).SetNoDataValue(no_data_list[i])

    return merged_ds

def ds_to_fileinfos(datasets:list["Dataset"]) -> list[file_info]:
    file_infos = []

    for ds in datasets:
        fi = file_info()
        fi.init_from_ds(ds)
        file_infos.append(fi)

    return file_infos

# def init_from_ds(ds:"Dataset") -> file_info:
#     fi = file_info()
#     fi.filename = ds.GetDescription()
#     fi.bands = ds.RasterCount
#     fi.xsize = ds.RasterXSize
#     fi.ysize = ds.RasterYSize
#     fi.band_type = ds.GetRasterBand(1).DataType
#     fi.projection = ds.GetProjection()
#     fi.geotransform = ds.GetGeoTransform()
#     fi.ulx = fi.geotransform[0]
#     fi.uly = fi.geotransform[3]
#     fi.lrx = fi.ulx + fi.geotransform[1] * fi.xsize
#     fi.lry = fi.uly + fi.geotransform[5] * fi.ysize
#
#     ct = ds.GetRasterBand(1).GetRasterColorTable()
#     if ct is not None:
#         fi.ct = ct.Clone()
#     else:
#         fi.ct = None
#
#     return fi

def mosaic_by_file_paths(tile_paths:list[str]) -> "Dataset":
    file_infos = names_to_fileinfos(tile_paths)
    return mosaic_tiles(file_infos)

def mosaic_by_ds(datasets:list["Dataset"]) -> "Dataset":
    file_infos = ds_to_fileinfos(datasets)
    return mosaic_tiles(file_infos)

def mosaic_tiles(file_infos:list[file_info]) -> "Dataset":

    ulx = file_infos[0].ulx
    uly = file_infos[0].uly
    lrx = file_infos[0].lrx
    lry = file_infos[0].lry

    for fi in file_infos:
        ulx = min(ulx, fi.ulx)
        uly = max(uly, fi.uly)
        lrx = max(lrx, fi.lrx)
        lry = min(lry, fi.lry)

    psize_x = file_infos[0].geotransform[1]
    psize_y = file_infos[0].geotransform[5]

    geotransform = [ulx, psize_x, 0, uly, 0, psize_y]

    xsize = int((lrx - ulx) / psize_x + 0.5)
    ysize = int((lry - uly) / psize_y + 0.5)

    bands = file_infos[0].bands
    band_type = file_infos[0].band_type

    driver = gdal.GetDriverByName('MEM')
    mem_ds = driver.Create('', xsize, ysize, bands, band_type)

    mem_ds.SetGeoTransform(geotransform)
    mem_ds.SetProjection(file_infos[0].projection)

    for fi in file_infos:
        for band in range(1, bands + 1):
            fi.copy_into(mem_ds, band, band)

    return mem_ds