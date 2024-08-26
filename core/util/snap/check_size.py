from typing import TYPE_CHECKING

from core.util.snap import find_boundary_from_product

if TYPE_CHECKING:
    from core.raster import Raster
    from esa_snappy import Product

def is_bigtiff_gpf(product):

    product_size = product.getRasterDataNode(product.getBandNames()[0]).getRasterWidth() * \
                   product.getRasterDataNode(product.getBandNames()[0]).getRasterHeight() * \
                   len(product.getBandNames()) * 4

    if product_size > 4 * 1024 * 1024 * 1024:
        return True
    return False

def get_image_spec_gpf(product:'Product') -> dict:
    width = product.getSceneRasterWidth()
    height = product.getSceneRasterHeight()

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

def get_geo_spec_gpf(product:'Product') -> dict:
    geo_spec = find_boundary_from_product(product)

    ul_x = geo_spec['ul_x']
    ul_y = geo_spec['ul_y']
    ur_x = geo_spec['lr_x']
    ur_y = geo_spec['ul_y']
    ll_x = geo_spec['ul_x']
    ll_y = geo_spec['lr_y']
    lr_x = geo_spec['lr_x']
    lr_y = geo_spec['lr_y']

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