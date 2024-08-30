import re
from esa_snappy import Product, jpy, ProductIO, ProductData
from core.raster import OUT_TYPE_MAP

def create_product(product_name:str, file_format:str, width:int, height:int):

    product_type = OUT_TYPE_MAP[file_format]
    product = Product(product_name, product_type, width, height)
    writer = ProductIO.getProductWriter(product_type)
    product.setProductWriter(writer)

    return product

def create_product_data(band_arr, arr_dtype:str):

    height, width = band_arr.shape
    pdata = ProductData.createInstance(ProductData.getType(arr_dtype), width * height)
    if arr_dtype == 'int16':
        arr_dtype = 'short'
    bjarr = jpy.array(arr_dtype, band_arr.flatten())
    pdata.setElems(bjarr)

    return pdata