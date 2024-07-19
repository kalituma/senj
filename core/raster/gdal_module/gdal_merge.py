import numpy as np
from typing import Union, TYPE_CHECKING
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