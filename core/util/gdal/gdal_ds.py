import numpy as np
from osgeo import gdal

from core.util.gdal import GDAL_DTYPE_MAP, read_gdal_bands

def create_ds(gdal_format, width, height, band_num, dtype, proj_wkt:str, transform:tuple, metadata=None,
              out_path='', is_bigtiff=False, compress=False):

    if isinstance(dtype, str):
        gdal_dtype = GDAL_DTYPE_MAP[dtype]
    else:
        gdal_dtype = dtype

    options = []
    if is_bigtiff:
        options.append('BigTIFF=YES')
    if compress:
        options.append('COMPRESS=LZW')

    driver = gdal.GetDriverByName(gdal_format)
    if len(options) > 0:
        new_ds = driver.Create(out_path, width, height, band_num, gdal_dtype, options=options)
    else:
        new_ds = driver.Create(out_path, width, height, band_num, gdal_dtype)

    new_ds.SetProjection(proj_wkt)
    new_ds.SetGeoTransform(transform)
    if metadata is not None:
        new_ds.SetMetadata(metadata)
    return new_ds

def create_ds_with_arr(arr:np.ndarray, gdal_format,
                       proj_wkt:str, transform:tuple, metadata:dict=None,
                       out_path='', is_bigtiff=False, compress=False):

    band_num, arr_height, arr_width = arr.shape
    dtype = arr.dtype.name

    mem_ds = create_ds(gdal_format, arr_width, arr_height,
                       band_num=band_num, dtype=dtype,
                       proj_wkt=proj_wkt, transform=transform,
                       metadata=metadata, out_path=out_path,
                       is_bigtiff=is_bigtiff, compress=compress)
    mem_ds.WriteArray(arr)
    mem_ds.FlushCache()

    return mem_ds

def create_ds_with_dict(raster_bands:dict[str], gdal_format,
                        proj_wkt:str, transform:tuple,
                        selected_band:list[str]=None, metadata=None,
                        out_path='', is_bigtiff=False, compress=False):

    if selected_band:
        s_bands = {bname : raster_bands[bname] for bname in selected_band}
    else:
        s_bands = raster_bands

    first_band_key = list(s_bands.keys())[0]
    first_band = s_bands[first_band_key]['value']
    dtype = first_band.dtype.name
    band_num = len(s_bands)

    mem_ds = create_ds(gdal_format, first_band.shape[1], first_band.shape[0],
                       band_num=band_num, dtype=dtype,
                       proj_wkt=proj_wkt, transform=transform,
                       metadata=metadata, out_path=out_path,
                       is_bigtiff=is_bigtiff, compress=compress)

    for b_idx, (band_name, band_elem_dict) in zip(range(1, band_num+1), s_bands.items()):
        b = mem_ds.GetRasterBand(b_idx)
        b.SetNoDataValue(band_elem_dict['no_data'])
        b.WriteArray(band_elem_dict['value'])

    mem_ds.FlushCache()
    return mem_ds

def copy_ds(src_ds, target_ds_type, selected_index:list[int]=None, out_path:str=None, is_bigtiff=False, compress=False):
    if not out_path:
        out_path = ''

    driver = gdal.GetDriverByName(target_ds_type)

    if selected_index:
        no_data_vals, bands = read_gdal_bands(src_ds, selected_index)

        tar_ds = create_ds(
            target_ds_type, src_ds.RasterXSize, src_ds.RasterYSize,
            len(selected_index), src_ds.GetRasterBand(1).DataType,
            src_ds.GetProjection(), src_ds.GetGeoTransform(), src_ds.GetMetadata(),
            out_path, is_bigtiff, compress
        )

        if bands.ndim == 2:
            bands = np.expand_dims(bands, axis=0)

        for i, no_data in enumerate(no_data_vals):

            tar_ds.GetRasterBand(i+1).SetNoDataValue(no_data if no_data is not None else 0)
            tar_ds.GetRasterBand(i+1).WriteArray(bands[i])
    else:
        tar_ds = driver.CreateCopy(out_path, src_ds)

    tar_ds.FlushCache()

    return tar_ds