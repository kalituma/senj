import numpy as np
from tqdm import tqdm
import re
from typing import TYPE_CHECKING, List

from core.util import assert_bnames, get_contained_list_map, load_snap
from core.util.errors import ContainedBandError
from core.util.snap import create_product_data

if TYPE_CHECKING:
    from esa_snappy import Product, Band

def rename_bands(product:"Product", band_names:List) -> "Product":
    product_bands = list(product.getBandNames())

    # assert len(band_names) == len(product.getBandNames()), 'The number of band names should be the same as the source product'
    if band_names == product_bands:
        return product

    contained_target_map = get_contained_list_map(product_bands, band_names)

    for contained_band, target_index in contained_target_map.items():
        product_bands[target_index] = f'{contained_band}_1'
        product.getBand(contained_band).setName(f'{contained_band}_1')

    for new_bname, old_bname in zip(band_names, product_bands):
        if new_bname != old_bname:
            product.getBand(old_bname).setName(new_bname)
    return product

def add_band_to_product(product, bands:dict):

    ProductData = load_snap('ProductData')

    for band_name, band_elem_dict in bands.items():
        band_arr = band_elem_dict['value']
        arr_dtype = band_arr.dtype.name
        # bnum_pattern = '[a-z]+'
        # arr_dtype = re.search(bnum_pattern, arr_dtype).group()

        if 'uint' in arr_dtype:
            band_arr = band_arr.astype('int16')
            arr_dtype = 'int16'

        # if 'float' in arr_dtype:
        #     arr_dtype = 'float32'

        p_dtype = ProductData.getType(arr_dtype)
        raster_data = create_product_data(band_arr, arr_dtype)

        if isinstance(band_name, int):
            band_name = f'{band_name}'
        band = product.addBand(band_name, p_dtype)
        if band_elem_dict['no_data'] is not None:
            band.setNoDataValue(band_elem_dict['no_data'])
        else:
            band.setNoDataValue(0)
        band.setRasterData(raster_data)
        band = None

    return product

def copy_product(src_product, selected_bands:list=None, copy_tie_point:bool=True) -> "Product":

    Product = load_snap('Product')
    ProductUtils = load_snap('ProductUtils')

    if selected_bands:
        matched_band = selected_bands
        for bname in matched_band:
            assert (bname in src_product.getBandNames()), f'Selected bands are not in the source product: {bname}'

    else:
        matched_band = src_product.getBandNames()

    if len(matched_band) == 0:
        raise ContainedBandError(list(matched_band))

    target_band = src_product.getBand(matched_band[0])
    width, height = target_band.getRasterWidth(), target_band.getRasterHeight()
    new_product = Product(src_product.getName(), src_product.getProductType(), width, height)
    new_product.setSceneGeoCoding(target_band.getGeoCoding())

    ProductUtils.copyMetadata(src_product, new_product)
    if copy_tie_point:
        ProductUtils.copyTiePointGrids(src_product, new_product)
        
    # ProductUtils.copyMasks(src_product, new_product)
    # ProductUtils.copyFlagBands(src_product, new_product, True)

    for target_band_name in matched_band:
        ProductUtils.copyBand(target_band_name, src_product, new_product, True)
        # target_band = src_product.getBand(target_band_name)
        # new_product.addBand(target_band)

    return new_product

def _get_band_grid(band:"Band") -> dict:

    jpy = load_snap('jpy')
    PixelPos = load_snap('PixelPos')

    band_size = {}

    DIR_POS = jpy.get_type('org.geotools.geometry.DirectPosition2D')

    width = band.getRasterSize().width
    height = band.getRasterSize().height

    band_size['width'] = width
    band_size['height'] = height

    affine = band.getGeoCoding().getImageToMapTransform()
    min_x, max_y = list(affine.transform(DIR_POS(PixelPos(0, 0)), None).getCoordinate())
    max_x, min_y = list(affine.transform(DIR_POS(PixelPos(width, height)), None).getCoordinate())

    band_size['min_x'], band_size['max_y'] = min_x, max_y
    band_size['max_x'], band_size['min_y'] = max_x, min_y

    band_size['x_res'] = (max_x - min_x) / width
    band_size['y_res'] = (max_y - min_y) / height
    band_size['projection'] = band.getGeoCoding().getMapCRS().toWKT()

    assert band_size['x_res'] == band_size['y_res'], 'X and Y resolution are not equal.'

    return band_size

def get_band_grid_size_gpf(product:"Product", selected_bands:list=None) -> dict:

    size_meta = {}

    if not selected_bands:
        selected_bands = list(product.getBandNames())

    assert_bnames(selected_bands, list(product.getBandNames()), 'Selected bands are not in the source product')

    for band_name in selected_bands:
        band = product.getBand(band_name)
        grid_size = _get_band_grid(band)
        size_meta[band_name] = grid_size

    return size_meta