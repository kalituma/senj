import numpy as np
from typing import Union, TYPE_CHECKING

from osgeo_utils.gdal_merge import names_to_fileinfos
from osgeo import gdal

from core.raster.gdal_module import read_gdal_bands, create_ds_with_arr
from core.util import assert_ds_equal

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

def merge(datasets:list["Dataset"], sbands:list[Union[list[int], None]], cobands:list[Union[list[int], None]]):
    assert len(datasets) == len(sbands) and len(datasets) == len(cobands), 'The number of products and selected bands must be the same'
    assert_ds_equal(datasets)

    band_list = []
    for ds, sband, cband in zip(datasets, sbands, cobands):
        if cband:
            selected_bands = cband
        elif sband:
            selected_bands = sband
        else:
            selected_bands = list(range(1, ds.RasterCount + 1))

        band_arr = read_gdal_bands(ds, selected_bands)
        if band_arr.ndim != 3:
            band_arr = band_arr[np.newaxis, :, :]
        band_list.append(band_arr)
    concat_band = np.concatenate(band_list, axis=0)

    merged_ds = create_ds_with_arr(concat_band, gdal_format='MEM', proj_wkt=datasets[0].GetProjection(), transform=datasets[0].GetGeoTransform())
    return merged_ds

def mosaic_tiles(tile_paths:list) -> "Dataset":

    file_infos = names_to_fileinfos(tile_paths)

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