import re
import numpy as np
from typing import Tuple, TYPE_CHECKING

from core.util import assert_bnames, load_snap
from core.util.errors import ContainedBandError
from core.util.snap import build_read_params

if TYPE_CHECKING:
    from esa_snappy import Product

def get_selected_bands_names(src_bnames:list[str], selected_bnames:list[str]=None, bname_word_included:bool=False):
    selected = []
    search_format = '{}(?:_|$)'
    if selected_bnames:
        for bname in selected_bnames:
            for src_bname in src_bnames:
                if bname_word_included:
                    if re.search(search_format.format(bname), src_bname):
                        selected.append(src_bname)
                else:
                    if bname == src_bname:
                        selected.append(src_bname)
                        break
    else:
        selected = src_bnames.copy()

    if len(selected) == 0:
        raise ContainedBandError(selected_bnames)

    return selected

def read_gpf(in_path:str) -> "Product":
    GPF = load_snap('GPF')
    params = build_read_params(file=in_path)
    product = GPF.createProduct('Read', params)
    return product

def read_gpf_bands_as_dict(product, selected_bands:list[str]=None) -> Tuple[dict, list[str]]:

    ProductData = load_snap('ProductData')
    result = {}

    if not selected_bands:
        selected_bands = list(product.getBandNames())

    assert_bnames(selected_bands, product.getBandNames(), msg=f'{selected_bands} is not in {list(product.getBandNames())}')

    for band_name in selected_bands:
        band_dict = {}
        band = product.getBand(band_name)
        no_data = band.getNoDataValue()
        band_dict['no_data'] = no_data
        if not band.hasRasterData():
            band.readRasterDataFully()
        b_width = band.getRasterWidth()
        b_height = band.getRasterHeight()
        data_type_str = ProductData.getTypeString(band.getDataType())
        band_dict['value'] = np.array(band.getRasterData().getElems(), dtype=np.dtype(data_type_str)).reshape(b_height, b_width)
        result[band_name] = band_dict

    return result, selected_bands
