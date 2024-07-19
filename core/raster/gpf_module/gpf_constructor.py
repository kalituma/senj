import re
from esa_snappy import Product, jpy, ProductIO, ProductData
from core.raster import OUT_TYPE_MAP

def create_product(product_name:str, file_format:str, width:int, height:int):

    product_type = OUT_TYPE_MAP[file_format]
    product = Product(product_name, product_type, width, height)
    writer = ProductIO.getProductWriter(product_type)
    product.setProductWriter(writer)

    return product

def create_product_data(band_arr):

    bnum_pattern = '[a-z]+'

    height, width = band_arr.shape
    data_type = band_arr.dtype.name
    pdata = ProductData.createInstance(ProductData.getType(data_type), width * height)
    data_type = re.search(bnum_pattern, data_type).group().replace('uint', 'short')
    bjarr = jpy.array(data_type, band_arr.flatten())
    pdata.setElems(bjarr)

    return pdata