import re
import numpy as np
from typing import Tuple
from pathlib import Path
from esa_snappy import GPF, Product, ProductData

from core.util import read_pickle, assert_bnames
from core.util.errors import ContainedBandError
from core.raster.gpf_module import build_read_params, set_meta_to_product, make_meta_dict

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

def load_raster_gpf(in_path, selected_bands:list[str]=None, bname_word_included=False) -> Tuple[dict, Product, list[str]]:

    path_ext = Path(in_path).suffix[1:]

    meta_dict = None

    params = build_read_params(file=in_path)
    product = GPF.createProduct('Read', params)

    src_bnames = list(product.getBandNames())

    selected_bands = get_selected_bands_names(src_bnames, selected_bands, bname_word_included)

    if path_ext == 'tif':
        pkl_path = in_path.replace('.tif', '.pkl')
        if Path(pkl_path).exists():
            meta_dict = read_pickle(pkl_path)

        if meta_dict:
            set_meta_to_product(product, meta_dict)
    else:
        meta_dict = make_meta_dict(product)

    return meta_dict, product, selected_bands

def read_gpf_bands_as_dict(product, selected_bands:list[str]=None) -> Tuple[dict, list[str]]:
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
