from esa_snappy import Product, GPF
from core.util.snap import build_reproject_params

def reproject_gpf(product:Product, params:dict):
    rp_params = build_reproject_params(**params)
    sf_product = GPF.createProduct('Reproject', rp_params, product)
    return sf_product