from typing import TYPE_CHECKING
from core.util.snap import add_band_to_product

if TYPE_CHECKING:
    from esa_snappy import Product

def del_bands_from_product(product:"Product", target_band_list) -> "Product":
    for band_name in target_band_list:
        src_band = product.getBand(band_name)
        product.removeBand(src_band)
    return product

def copy_cached_to_raw_gpf(product, cached_band:dict) -> "Product":

    # t_band = product.getBand(band_name)
    return add_band_to_product(product, cached_band)