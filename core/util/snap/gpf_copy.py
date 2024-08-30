from esa_snappy import Product
from core.util.snap import add_band_to_product

def copy_cached_to_raw_gpf(product, cached_band:dict) -> Product:

    # t_band = product.getBand(band_name)

    for band_name in cached_band:
        src_band = product.getBand(band_name)
        product.removeBand(src_band)

    return add_band_to_product(product, cached_band)