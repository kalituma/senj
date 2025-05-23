import numpy as np

from core import LAMBDA
from core.util import load_gdal, load_ogr

def get_raster_envelope(raster_raw) -> tuple[float, float, float, float, float, float, float, float]:
    gt = raster_raw.GetGeoTransform()
    cols = raster_raw.RasterXSize
    rows = raster_raw.RasterYSize

    ulx, uly = gt[0], gt[3]
    urx, ury = gt[0] + cols * gt[1], gt[3] + cols * gt[2]
    lrx, lry = gt[0] + cols * gt[1] + rows * gt[4], gt[3] + cols * gt[2] + rows * gt[5]
    llx, lly = gt[0] + rows * gt[4], gt[3] + rows * gt[5]

    return ulx, uly, urx, ury, lrx, lry, llx, lly

def is_bigtiff_gdal(ds):

    gdal = load_gdal()

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

def create_geom(wkt):
    ogr = load_ogr()
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

def get_band_grid_size_gdal(ds, band_name, selected_index=None):
    size_meta = {}

    if not selected_index:
        selected_index = list(range(1, ds.RasterCount + 1))

    for band_num in selected_index:
        b_idx = band_num - 1
        band = ds.GetRasterBand(band_num)
        gt = ds.GetGeoTransform()

        band_size = {}

        band_size['width'] = band.XSize
        band_size['height'] = band.YSize
        band_size['x_res'] = gt[1]
        band_size['y_res'] = -gt[5]
        band_size['min_x'] = gt[0]
        band_size['max_y'] = gt[3]
        band_size['max_x'] = gt[0] + band_size['width'] * gt[1]
        band_size['min_y'] = gt[3] + band_size['height'] * gt[5]
        band_size['projection'] = ds.GetProjection()
        size_meta[band_name[b_idx]] = band_size

    return size_meta

def get_image_spec_gdal(ds):
    width = ds.RasterXSize
    height = ds.RasterYSize

    ul_col = float(0.0)
    ul_row = float(0.0)
    ur_col = float(width - 1)
    ur_row = float(0.0)
    lr_col = ur_col
    lr_row = float(height - 1)
    ll_col = float(0.0)
    ll_row = lr_row

    return {
        'ul_col': ul_col,
        'ul_row': ul_row,
        'ur_col': ur_col,
        'ur_row': ur_row,
        'lr_col': lr_col,
        'lr_row': lr_row,
        'll_col': ll_col,
        'll_row': ll_row
    }

def get_geo_spec_gdal(ds):
    gt = ds.GetGeoTransform()
    x_res = gt[1]
    y_res = gt[5]

    ul_x = gt[0]
    ul_y = gt[3]
    ur_x = gt[0] + x_res * ds.RasterXSize
    ur_y = ul_y

    ll_x = ul_x
    ll_y = gt[3] + y_res * ds.RasterYSize
    lr_x = ur_x
    lr_y = ll_y

    return {
        'ul_x': ul_x,
        'ul_y': ul_y,
        'ur_x': ur_x,
        'ur_y': ur_y,
        'll_x': ll_x,
        'll_y': ll_y,
        'lr_x': lr_x,
        'lr_y': lr_y
    }

@LAMBDA.reg(name='create_dem')
def create_dem(in_ds, out_ds, out_bounds, column_name, ref_cols, ref_rows, algorithm='linear'):
    gdal = load_gdal()
    ulx, uly, lrx, lry = out_bounds

    out_ds = gdal.Grid(out_ds, in_ds, outputBounds=[ulx, uly, lrx, lry],
                       zfield=column_name, algorithm=algorithm, width=ref_cols, height=ref_rows)
    return out_ds

@LAMBDA.reg(name='create_slope')
def create_slope(in_ds, out_ds):
    gdal = load_gdal()
    out_ds = gdal.DEMProcessing(out_ds, in_ds, 'slope')
    return out_ds