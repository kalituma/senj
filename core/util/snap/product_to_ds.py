import numpy as np
from typing import TYPE_CHECKING
from core.util import load_snap

if TYPE_CHECKING:
    from esa_snappy import Product, Band, CrsGeoCoding

from core.util import epsg_to_wkt, transform_coords

def find_epsg_from_product(product:"Product") -> int:
    jpy = load_snap('jpy')
    Product = load_snap('Product')


    CRS = jpy.get_type('org.geotools.referencing.CRS')
    return CRS.lookupEpsgCode(Product.findModelCRS(product.getSceneGeoCoding()), True)

def find_proj_from_product(product:"Product") -> str:
    Product = load_snap('Product')

    product_geocoding = product.getSceneGeoCoding()
    wkt = Product.findModelCRS(product_geocoding).toWKT()
    return wkt

def find_proj_from_band(band:"Band") -> str:
    Product = load_snap('Product')

    band_geocoding = band.getGeoCoding()
    wkt = Product.findModelCRS(band_geocoding).toWKT()
    if '(DD)' in wkt:
        wkt = epsg_to_wkt(4326)
    return wkt

def find_boundary_from_product(product:"Product", epsg:int=4326) -> dict:

    jpy = load_snap('jpy')
    PixelPos = load_snap('PixelPos')

    DIR_POS = jpy.get_type('org.geotools.geometry.DirectPosition2D')
    b_width, b_height = product.getSceneRasterWidth(), product.getSceneRasterHeight()
    affine = product.getSceneGeoCoding().getImageToMapTransform()

    min_x, max_y = list(affine.transform(DIR_POS(PixelPos(0, 0)), None).getCoordinate())
    max_x, min_y = list(affine.transform(DIR_POS(PixelPos(product.getSceneRasterWidth(), product.getSceneRasterHeight())), None).getCoordinate())
    # max_x, min_y = list(affine.transform(DIR_POS(PixelPos(product.getSceneRasterWidth()-0.5, product.getSceneRasterHeight()-0.5)), None).getCoordinate())


    if epsg != 4326:
        max_y, min_x = transform_coords(min_x, max_y, epsg, 4326)
        min_y, max_x = transform_coords(max_x, min_y, epsg, 4326)

    x_res = (max_x - min_x) / b_width
    y_res = -(max_y - min_y) / b_height

    return {
        'ul_x': min_x,
        'ul_y': max_y,
        'lr_x': max_x,
        'lr_y': min_y,
        'res_x': x_res,
        'res_y': y_res
    }

def find_gt_from_product(product:"Product") -> list:

    jpy = load_snap('jpy')
    PixelPos = load_snap('PixelPos')

    DIR_POS = jpy.get_type('org.geotools.geometry.DirectPosition2D')
    b_width, b_height = product.getSceneRasterWidth(), product.getSceneRasterHeight()

    affine = product.getSceneGeoCoding().getImageToMapTransform()
    min_x, max_y = list(affine.transform(DIR_POS(PixelPos(0, 0)), None).getCoordinate())
    max_x, min_y = list(affine.transform(DIR_POS(PixelPos(b_width, b_height)), None).getCoordinate())
    x_res = (max_x - min_x) / b_width
    y_res = -(max_y - min_y) / b_height
    b_geotransform = [min_x, x_res, 0, max_y, 0, y_res]

    return b_geotransform

def find_gt_from_band(band:"Band") -> list:

    jpy = load_snap('jpy')
    PixelPos = load_snap('PixelPos')

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

def find_geocoding_from_wkt(wkt:str, gt:tuple, width:int, height:int) -> "CrsGeoCoding":

    jpy = load_snap('jpy')
    CrsGeoCoding = load_snap('CrsGeoCoding')

    CRS = jpy.get_type('org.geotools.referencing.CRS')
    map_csr = CRS.parseWKT(wkt)
    min_x, res_x, _, max_y, _, res_y = gt
    res_y = -res_y

    return CrsGeoCoding(map_csr, width, height, min_x + res_x/2, max_y - res_y/2, res_x, res_y)