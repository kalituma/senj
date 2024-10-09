from typing import TYPE_CHECKING
from core.util import load_snap
from core.util.snap import build_subset_params

if TYPE_CHECKING:
    from esa_snappy import Product

def subset_gpf(product:"Product", params:dict):
    GPF = load_snap('GPF')
    subset_params = build_subset_params(**params)
    subset_product = GPF.createProduct('Subset', subset_params, product)
    return subset_product
