import numpy as np
from typing import TYPE_CHECKING
from core.util import load_snap

if TYPE_CHECKING:
    from esa_snappy import Product

def build_grid_meta_from_gpf(product:"Product", det_name:str):

    jpy = load_snap('jpy')
    PixelPos = load_snap('PixelPos')

    grid = {}

    DIR_POS = jpy.get_type('org.geotools.geometry.DirectPosition2D')

    width = product.getBand(det_name).getRasterSize().width
    height = product.getBand(det_name).getRasterSize().height

    affine = product.getBand(det_name).getGeoCoding().getImageToMapTransform()
    min_x, max_y = list(affine.transform(DIR_POS(PixelPos(0, 0)), None).getCoordinate())
    max_x, min_y = list(affine.transform(DIR_POS(PixelPos(width, height)), None).getCoordinate())

    grid['NCOLS'] = width
    grid['NROWS'] = height
    grid['ULX'] = min_x
    grid['ULY'] = max_y

    grid['XDIM'] = np.round((max_x - min_x) / width)
    grid['YDIM'] = -np.round((max_y - min_y) / height)
    grid['RESOLUTION'] = grid['XDIM']

    return grid