import numpy as np
from esa_snappy import Product, jpy, PixelPos, Band, CrsGeoCoding

def find_proj_from_band(band:Band) -> str:

    band_geocoding = band.getGeoCoding()
    wkt = Product.findModelCRS(band_geocoding).toWKT()
    return wkt

def find_gt_from_band(band:Band) -> list:

    DIR_POS = jpy.get_type('org.geotools.geometry.DirectPosition2D')
    b_width, b_height = band.getRasterWidth(), band.getRasterHeight()

    band_geocoding = band.getGeoCoding()
    affine = band_geocoding.getImageToMapTransform()
    min_x, max_y = list(affine.transform(DIR_POS(PixelPos(0, 0)), None).getCoordinate())
    max_x, min_y = list(affine.transform(DIR_POS(PixelPos(b_width, b_height)), None).getCoordinate())
    x_res = (max_x - min_x) / b_width
    y_res = -(max_y - min_y) / b_height
    b_geotransform = [min_x, x_res, 0, max_y, 0, y_res]

    return b_geotransform

def find_geocoding_from_wkt(wkt:str, gt:tuple, width:int, height:int) -> CrsGeoCoding:
    CRS = jpy.get_type('org.geotools.referencing.CRS')
    map_csr = CRS.parseWKT(wkt)
    min_x, res_x, _, max_y, _, res_y = gt
    res_y = -res_y

    return CrsGeoCoding(map_csr, width, height, min_x + res_x/2, max_y - res_y/2, res_x, res_y)