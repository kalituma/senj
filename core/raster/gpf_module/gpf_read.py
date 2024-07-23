import re
import numpy as np
from typing import Tuple
from pathlib import Path
from esa_snappy import GPF, Product, ProductData

from core.util import read_pickle, assert_bnames
from core.util.errors import BandError
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
        raise BandError(selected_bnames)

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

def read_det(product, bands:list[str]=None):

    if bands is None:
        bands = DET_BANDS

    f = product.getFileLocation()
    det_dict = {}
    if '.SAFE' in f.toString():
        for band_name in bands:
            det_name_frame = f'B_detector_footprint_{band_name}'
            det_band = product.getBand(det_name_frame)
            det_band.readRasterDataFully()
            b_width = det_band.getRasterWidth()
            b_height = det_band.getRasterHeight()
            det_dict[band_name] = np.array(det_band.getRasterData().getElems()).reshape(b_height, b_width)
    elif '.dim' in f.toString():
        par_loc = f.toString().replace('.dim', '.data')
        for band_name in bands:
            band_num = int(band_name[1:])
            det_loc_frame = f'{par_loc}/ORI_DET/MSK_DETFOO_B{band_num:02}.jp2'
            ds = gdal.Open(det_loc_frame)
            arr = ds.ReadAsArray()
            det_dict[band_name] = arr

    return det_dict