from typing import Union, Tuple, List, TYPE_CHECKING, Optional
import numpy as np
from osgeo import gdal, ogr, osr

if TYPE_CHECKING:
    from osgeo.gdal import Dataset
    from osgeo.ogr import DataSource, FieldDefn, Layer

from core.util.gdal import GDAL_DTYPE_MAP, read_gdal_bands

def create_datasource(path: str, ogr_format: str = 'ESRI Shapefile'):
    driver = ogr.GetDriverByName(ogr_format)    
    if driver.Open(path):
        driver.DeleteDataSource(path)    
    return driver.CreateDataSource(path)

def create_ds(gdal_format=None, width=None, height=None, band_num=None, dtype=None, 
              proj_wkt:str=None, transform:tuple=None, metadata=None,
              out_path='', is_bigtiff=False, compress=False, no_data=np.nan, 
              is_vector=False, geom_type=None, field_defs=None):
    if is_vector:
        return create_vector_ds(gdal_format, proj_wkt, out_path, geom_type, field_defs, metadata)
    else:
        return create_raster_ds(gdal_format, width, height, band_num, dtype, proj_wkt, 
                                transform, metadata, out_path, is_bigtiff, compress, no_data)

def create_raster_ds(gdal_format, width, height, band_num, dtype, proj_wkt:str=None, 
                    transform:tuple=None, metadata=None, out_path='', 
                    is_bigtiff=False, compress=False, no_data=np.nan):    
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

    if proj_wkt is not None:
        new_ds.SetProjection(proj_wkt)
    if transform is not None:
        new_ds.SetGeoTransform(transform)
    if metadata is not None:
        new_ds.SetMetadata(metadata)

    for i in range(band_num):
        new_ds.GetRasterBand(i+1).SetNoDataValue(no_data)
        new_ds.GetRasterBand(i+1).Fill(no_data)

    return new_ds

def create_vector_ds(gdal_format: str = 'Memory', proj_wkt: Optional[str] = None, 
                     out_path: str = '', geom_type: Optional[int] = ogr.wkbPolygon,
                     field_defs: Optional[List["FieldDefn"]] = None,
                     metadata: Optional[dict] = None) -> 'DataSource':
    
    if not gdal_format:
        gdal_format = 'Memory'
    if not geom_type:
        geom_type = ogr.wkbPolygon
    if not field_defs:
        field_defs = []
        
    driver = gdal.GetDriverByName(gdal_format)
    ds = driver.Create(out_path if out_path else "", 0, 0, 0, gdal.GDT_Unknown, [])
    
    layer_name = "layer0" if gdal_format == 'Memory' else ""
    srs = None
    if proj_wkt:
        srs = osr.SpatialReference()
        srs.ImportFromWkt(proj_wkt)
    
    layer = ds.CreateLayer(layer_name, srs, geom_type)
    
    for field_defn in field_defs:
        layer.CreateField(field_defn)
    
    if metadata:
        for key, value in metadata.items():
            ds.SetMetadataItem(key, value)
    
    return ds

def create_ds_with_layer(layer: "Layer", gdal_format, out_path=''):
    driver = ogr.GetDriverByName(gdal_format)

    if driver.Open(out_path):
        driver.DeleteDataSource(out_path)
    
    out_ds = driver.CreateDataSource(out_path)
    out_ds.CreateLayer(layer.GetName(), layer.GetSpatialRef(), layer.GetGeomType())
    out_ds.FlushCache()
    out_ds = None

    return out_ds

def create_ds_with_arr(arr:np.ndarray, gdal_format,
                       proj_wkt:Union[str, None]=None, transform:Union[tuple, None]=None, metadata:dict=None,
                       out_path='', is_bigtiff=False, compress=False, no_data=np.nan):

    if arr.ndim == 2:
        arr = np.expand_dims(arr, axis=0)

    band_num, arr_height, arr_width = arr.shape
    dtype = arr.dtype.name

    if arr.dtype.itemsize < 4:
        arr[arr == no_data] = 0
    else:
        arr[arr == no_data] = np.nan

    mem_ds = create_ds(gdal_format, arr_width, arr_height,
                       band_num=band_num, dtype=dtype,
                       proj_wkt=proj_wkt, transform=transform,
                       metadata=metadata, out_path=out_path,
                       is_bigtiff=is_bigtiff, compress=compress,
                       no_data=no_data)
    mem_ds.WriteArray(arr)
    mem_ds.FlushCache()

    return mem_ds

def create_ds_with_dict(raster_bands:dict[str], gdal_format,
                        proj_wkt:str, transform:Union[Tuple, List], metadata=None,
                        out_path='', is_bigtiff=False, compress=False):

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

    btoi_for_ds = {}
    for b_idx, (band_name, band_elem_dict) in zip(range(1, band_num+1), s_bands.items()):
        b = mem_ds.GetRasterBand(b_idx)
        if band_elem_dict['no_data'] is not None:
            b.SetNoDataValue(band_elem_dict['no_data'])
        else:
            b.SetNoDataValue(0)
        b.WriteArray(band_elem_dict['value'])
        btoi_for_ds[band_name] = b_idx

    mem_ds.FlushCache()
    return mem_ds, btoi_for_ds

def copy_ds(src_ds, target_ds_type, selected_index:list[int]=None, out_path:str=None, is_bigtiff=False, compress=False) -> 'Dataset':
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

def read_vector_ds(path: str):
    return gdal.OpenEx(path, gdal.OF_VECTOR)

