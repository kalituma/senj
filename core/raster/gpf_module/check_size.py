def is_bigtiff_gpf(product):
    product_size = product.getRasterDataNode(product.getBandNames()[0]).getRasterWidth() * \
                   product.getRasterDataNode(product.getBandNames()[0]).getRasterHeight() * \
                   len(product.getBandNames()) * 4

    if product_size > 4 * 1024 * 1024 * 1024:
        return True
    return False