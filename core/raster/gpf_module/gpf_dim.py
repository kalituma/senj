from esa_snappy import GPF, Product
from core.raster.gpf_module import build_subset_params

def subset_gpf(product:Product, params:dict):

    subset_params = build_subset_params(**params)
    subset_product = GPF.createProduct('Subset', subset_params, product)
    return subset_product
