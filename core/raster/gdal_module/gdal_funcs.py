import numpy as np
from osgeo import gdal, osr, ogr

def make_transform(src_epsg, tar_epsg):
    source_spatial_ref = osr.SpatialReference()
    source_spatial_ref.ImportFromEPSG(src_epsg)
    target_spatial_ref = osr.SpatialReference()
    target_spatial_ref.ImportFromEPSG(tar_epsg)
    return osr.CoordinateTransformation(source_spatial_ref, target_spatial_ref)

def is_bigtiff_gdal(ds):
    width = ds.RasterXSize
    height = ds.RasterYSize
    bands = ds.RasterCount
    data_type = ds.GetRasterBand(1).DataType
    bytes_per_pixel = gdal.GetDataTypeSize(data_type) // 8

    estimated_size = width * height * bands * bytes_per_pixel

    if estimated_size > 4 * 1024 * 1024 * 1024:
        return True
    else:
        return False

def transform_coords(lon, lat, source_epsg, target_epsg):
    transformer = make_transform(source_epsg, target_epsg)
    x, y, z = transformer.TransformPoint(lat, lon)
    return x, y

def create_geom(wkt):
    geom = ogr.CreateGeometryFromWkt(wkt)
    return geom

def gt_from_gatts(gatts, band_name):

    res = gatts['band_data']['Resolution'][band_name]
    ul_x = gatts['gr_meta']['CUR_GRIDS'][res]['ULX']
    ul_y = gatts['gr_meta']['CUR_GRIDS'][res]['ULY']
    xdim = gatts['gr_meta']['CUR_GRIDS'][res]['XDIM']
    ydim = gatts['gr_meta']['CUR_GRIDS'][res]['YDIM']

    return (ul_x, xdim, 0, ul_y, 0, -ydim)


def _check_info_equal(gtiff_1, gtiff_2):
    return gtiff_1.gt_proj == gtiff_2.gt_proj and gtiff_1.gt_arr.shape == gtiff_2.gt_arr.shape


