from tqdm import tqdm
from esa_snappy import Product, ProductUtils, ProductData

from core.util.errors import BandError
from core.raster.gpf_module import create_product_data


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
        raise BandError(list(matched_band))

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