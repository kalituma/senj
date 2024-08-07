from osgeo import gdal

def build_grid_meta_from_gdal(ds:gdal.Dataset) -> dict:

    grid = {}
    grid['NCOLS'] = ds.RasterXSize
    grid['NROWS'] = ds.RasterYSize
    grid['ULX'] = ds.GetGeoTransform()[0]
    grid['ULY'] = ds.GetGeoTransform()[3]
    grid['XDIM'] = ds.GetGeoTransform()[1]
    grid['YDIM'] = ds.GetGeoTransform()[5]
    grid['RESOLUTION'] = grid['XDIM']
    return grid