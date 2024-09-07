from esa_snappy import Product, GPF
from core.util.snap import build_reproject_params
from core.util import epsg_to_wkt

def reproject_gpf(product:Product, params:dict):

    params['crs'] = epsg_to_wkt(int(params['crs'][5:]))
    rp_params = build_reproject_params(**params)
    sf_product = GPF.createProduct('Reproject', rp_params, product)
    return sf_product