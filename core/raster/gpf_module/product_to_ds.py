import numpy as np
from esa_snappy import Product, jpy, PixelPos

def find_proj_from_band(band):

    band_geocoding = band.getGeoCoding()
    wkt = Product.findModelCRS(band_geocoding).toWKT()
    return wkt

def find_gt_from_band(band):

    DIR_POS = jpy.get_type('org.geotools.geometry.DirectPosition2D')
    b_width, b_height = band.getRasterWidth(), band.getRasterHeight()

    band_geocoding = band.getGeoCoding()
    affine = band_geocoding.getImageToMapTransform()
    min_x, max_y = list(affine.transform(DIR_POS(PixelPos(0, 0)), None).getCoordinate())
    max_x, min_y = list(affine.transform(DIR_POS(PixelPos(b_width-1, b_height-1)), None).getCoordinate())
    x_res = (max_x - min_x) / b_width
    y_res = -(max_y - min_y) / b_height
    b_geotransform = [min_x, x_res, 0, max_y, 0, y_res]

    return b_geotransform