import numpy as np
from esa_snappy import GPF, Product, jpy

from core.util import assert_bnames
from core.raster.gpf_module import build_mosaic_params, find_epsg_from_product, find_boundary_from_product

def check_mosaic_assert(src_products):
    target_bnames = list(src_products[0].getBandNames())

    for src_product in src_products[1:]:
        assert_bnames(list(src_product.getBandNames()), target_bnames, 'The band names of the source products should be the same')
        assert len(target_bnames) == len(
            list(src_product.getBandNames())), 'The number of bands of the source products should be the same'
    assert_bnames(target_bnames, list(src_products[-1].getBandNames()), 'The band names of the source products should be the same')

def merge_spec(geo_specs:list):
    # find the largest boundary
    result_spec = {}
    for geo_spec in geo_specs:
        for key, value in geo_spec.items():
            if key not in result_spec:
                result_spec[key] = value
            else:
                if key == 'res_x' or key == 'res_y':
                    assert np.isclose(result_spec[key], value), f'The resolution of the source products should be the same'
                    continue
                if key in ['ul_x', 'lr_y']:
                    result_spec[key] = min(result_spec[key], value)
                else:
                    result_spec[key] = max(result_spec[key], value)
    return result_spec

def remove_count_bands(src_product:Product) -> Product:
    bands = list(src_product.getBands())
    for band in bands:
        if 'count' in band.getName().lower():
            src_product.removeBand(band)
    return src_product

def mosaic_gpf(src_products:list[Product], band_label_names:list[str] = None) -> Product:

    check_mosaic_assert(src_products)

    bname_list = list(src_products[0].getBandNames())
    if band_label_names:
        band_names = zip(bname_list, band_label_names)
    else:
        band_names = zip(bname_list, bname_list)

    scene_epsg = find_epsg_from_product(src_products[0])
    geo_specs = [find_boundary_from_product(src_product) for src_product in src_products]
    geo_spec = merge_spec(geo_specs)

    params = build_mosaic_params(variables=band_names, crs=f'epsg:{scene_epsg}', geo_spec=geo_spec, combine='AND')
    product = GPF.createProduct('Mosaic', params, src_products)
    product = remove_count_bands(product)

    return product