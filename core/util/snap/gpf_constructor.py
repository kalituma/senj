import re
from core.util import load_snap
from core.raster import OUT_TYPE_MAP

def create_product(product_name:str, file_format:str, width:int, height:int):

    Product = load_snap('Product')
    ProductIO = load_snap('ProductIO')

    product_type = OUT_TYPE_MAP[file_format]
    product = Product(product_name, product_type, width, height)
    writer = ProductIO.getProductWriter(product_type)
    product.setProductWriter(writer)

    return product

def create_product_data(band_arr, arr_dtype:str):

    ProductData = load_snap('ProductData')
    jpy = load_snap('jpy')

    height, width = band_arr.shape
    pdata = ProductData.createInstance(ProductData.getType(arr_dtype), width * height)
    if arr_dtype == 'int16':
        arr_dtype = 'short'
    if arr_dtype == 'float32':
        arr_dtype = 'float'
    bjarr = jpy.array(arr_dtype, band_arr.flatten())
    pdata.setElems(bjarr)

    return pdata