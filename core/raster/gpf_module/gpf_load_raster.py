import os
from typing import Tuple
from pathlib import Path
from esa_snappy import Product

from core.util import parse_meta_xml, read_pickle
from core.raster.gpf_module import read_gpf, get_selected_bands_names, mosaic_gpf, rename_bands
from core.raster import ProductType

def load_raster_gpf(in_path, product_type:ProductType, selected_bands:list[str]=None, bname_word_included=False) -> Tuple[Product, list[str], bool]:

    ext = Path(in_path).suffix.lower()
    tile_merged = False

    band_names = []
    band_rename = False
    if ext == '.xml':
        tmp_meta = parse_meta_xml(in_path, product_type)
        base_path = Path(in_path).parent
        if product_type == ProductType.WV:

            band_idx = [item['index'] for key, item in tmp_meta['BAND_INFO'].items()]
            band_names = [key for key, item in tmp_meta['BAND_INFO'].items()]
            band_names = [x for _, x in sorted(zip(band_idx, band_names))]
            band_rename = True

            tile_paths = [os.path.join(str(base_path), tile_info['FILENAME']) for tile_info in tmp_meta['TILE_INFO']]
            assert all([os.path.exists(tile_path) for tile_path in tile_paths]), f'All tile paths should be exist in {tile_paths}'
            ds_list = [read_gpf(tile_path) for tile_path in tile_paths]
            product = mosaic_gpf(ds_list)
            tile_merged = True
        else:
            raise NotImplementedError(f'Product type({product_type}) is not implemented for the input process.')
    elif ext == '.tif':
        meta_path = in_path.replace('.tif', '.pkl')
        if os.path.exists(meta_path):
            tmp_meta = read_pickle(meta_path)
            if 'band_to_index' in tmp_meta and 'index_to_band' in tmp_meta:
                band_idx = list(tmp_meta['index_to_band'].keys())
                band_names = list(tmp_meta['index_to_band'].values())
                band_names = [x for _, x in sorted(zip(band_idx, band_names))]
                band_rename = True

        product = read_gpf(in_path)
    else:
        product = read_gpf(in_path)

    if band_rename:
        product = rename_bands(product, band_names)

    src_bnames = list(product.getBandNames())
    selected_bands = get_selected_bands_names(src_bnames, selected_bands, bname_word_included)

    return product, selected_bands, tile_merged