from typing import Union
from esa_snappy import Product, GPF, HashMap, jpy
from copy import deepcopy
def get_merged_len_gpf(products:list[Product], sbands:Union[list[Union[list[str], None]], None], cobands:Union[list[list[str]], None]):
    len_sum = 0
    for product, sband, cband in zip(products, sbands, cobands):
        if cband:
            selected_bands = cband
        elif sband:
            selected_bands = sband
        else:
            selected_bands = list(product.getBandNames())
        len_sum += len(selected_bands)

    return len_sum

def change_valid_mask_expression(product:Product):
    band_names = list(product.getBandNames())
    for band_name in band_names:
        band = product.getBand(band_name)
        prev_bname = band_name.split('$')[1]
        band_valid_exp = band.getValidPixelExpression()
        new_band_valid_exp = band_valid_exp.replace(prev_bname, band_name)
        band.setValidPixelExpression(new_band_valid_exp)
    return product

def merge(products:list[Product], sbands:list[Union[list[str], None]], cobands:list[Union[list[str], None]]):
    assert len(products) == len(sbands), 'The number of products and selected bands must be the same'

    total_len = get_merged_len_gpf(products, sbands, cobands)
    node_desc = jpy.get_type("org.esa.snap.core.gpf.common.MergeOp$NodeDescriptor")
    included_bands = jpy.array("org.esa.snap.core.gpf.common.MergeOp$NodeDescriptor", total_len)

    src_products = HashMap()
    merge_params = HashMap()

    total_idx = 0
    for i, (product, sband, cband) in enumerate(zip(products, sbands, cobands)):

        if i == 0:
            product_id = f"masterProduct"
        else:
            product_id = f"slaveProduct_{i}"

        src_products.put(product_id, product)
        if cband:
            selected_bands = cband
        elif sband:
            selected_bands = sband
        else:
            selected_bands = list(product.getBandNames())

        for l_idx, band_name in enumerate(selected_bands):
            new_name = '$'.join([product_id, band_name])
            nd = node_desc()
            nd.setProductId(product_id)
            nd.setName(band_name)
            nd.setNewName(new_name)
            included_bands[total_idx] = nd
            total_idx += 1

    merge_params.put('includes', included_bands)
    merge_result = GPF.createProduct('Merge', merge_params, src_products)
    merge_result = change_valid_mask_expression(merge_result)

    return merge_result