import numpy as np
from tqdm import tqdm
from esa_snappy import jpy, Product, Band, ProductUtils, ProductData, PixelPos

from core.util import assert_bnames
from core.util.errors import ContainedBandError
from core.util.snap import create_product_data

def rename_bands(product:Product, band_names:list) -> Product:
    assert len(band_names) == len(product.getBandNames()), 'The number of band names should be the same as the source product'
    for new_bname, old_bname in zip(band_names, product.getBandNames()):
        product.getBand(old_bname).setName(new_bname)
    return product

def add_band_to_product(product, bands:dict):

    for band_name, band_elem_dict in tqdm(bands.items(), desc='Adding bands to raw dataset.'):
        band_arr = band_elem_dict['value']
        dtype = band_arr.dtype.name
        data_type = ProductData.getType(dtype)
        raster_data = create_product_data(band_arr)
        if isinstance(band_name, int):
            band_name = f'{band_name}'
        band = product.addBand(band_name, data_type)
        band.setNoDataValue(band_elem_dict['no_data'])
        band.setRasterData(raster_data)
        band = None

    return product

def copy_product(src_product, selected_bands:list=None):

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
    ProductUtils.copyTiePointGrids(src_product, new_product)
    # ProductUtils.copyMasks(src_product, new_product)
    # ProductUtils.copyFlagBands(src_product, new_product, True)

    for target_band_name in matched_band:
        target_band = src_product.getBand(target_band_name)
        new_product.addBand(target_band)

    return new_product

def _get_band_grid(band:Band) -> dict:

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

def get_band_grid_size_gpf(product:Product, selected_bands:list=None) -> dict:

    size_meta = {}

    if not selected_bands:
        selected_bands = list(product.getBandNames())

    assert_bnames(selected_bands, list(product.getBandNames()), 'Selected bands are not in the source product')

    for band_name in selected_bands:
        band = product.getBand(band_name)
        grid_size = _get_band_grid(band)
        size_meta[band_name] = grid_size

    return size_meta