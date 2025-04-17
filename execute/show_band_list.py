# from absl import app
# from absl import flags
# from absl import logging
import argparse
from logging import info
from pathlib import Path

from core.config import expand_var
from core.util import get_btoi_from_tif, read_pickle, parse_meta_xml, ProductType
from core.util.identify import identify_product
from core.util.gdal import read_single
from core.util.snap import read_gpf
from core.raster.funcs import load_images_paths

# flags.DEFINE_string('file', None, 'Name of the file to show the band list', short_name='f')
# flags.mark_flag_as_required('file')

ALLOWED_EXTENSIONS = ['.tif', '.xml', '.safe', '.dim']

def read_bands(file_path) -> list:
    ext = Path(file_path).suffix.lower()
    product_type, meta_path = identify_product(file_path)
    image_paths = load_images_paths(file_path, product_type)

    band_list = None
    raster_num = 0
    if ext == '.tif':
        if Path(meta_path).suffix == '.pkl':
            meta_dict = read_pickle(meta_path)
            if 'band_to_index' in meta_dict:
                band_list = list(meta_dict['band_to_index'].keys())

        if band_list is None:
            band_to_index = get_btoi_from_tif(file_path)
            if band_to_index is not None:
                band_list = list(band_to_index.keys())

        product = read_gpf(image_paths[0])
        if band_list is None:
            band_list = [b for b in list(product.getBandNames())]

        raster_num = product.getNumBands()

    elif ext == '.xml':
        meta_dict = parse_meta_xml(file_path, product_type)
        if product_type == ProductType.WV:
            band_list = [key for key in meta_dict['BAND_INFO']]
            raster_num = len(meta_dict['BAND_INFO'])
        elif product_type == ProductType.PS:
            tif_ds = read_single(image_paths[0])
            raster_num = tif_ds.RasterCount
        else:
            raise NotImplementedError(f'Product type({product_type}) is not implemented for the input process.')

    elif ext in ['.safe', '.dim']:
        product = read_gpf(image_paths[0])
        band_list = [b for b in list(product.getBandNames())]
        raster_num = product.getNumBands()
    else:
        raise NotImplementedError(f'File type not supported: {ext}')

    if band_list is None:
        band_indices = list(range(1, raster_num + 1))
        band_list = [f'band_{index}' for index in band_indices]

    return band_list


def main():

    parser = argparse.ArgumentParser(description='Show band list of the input file')
    parser.add_argument('-f', '--file', type=str, help='Name of the file to show the band list')
    flags = parser.parse_args()

    file_path = expand_var(flags.file)
    ext = Path(file_path).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        logging.error(f'File type not supported: %s, supported extensions are {ALLOWED_EXTENSIONS}', ext)
        return 1

    assert Path(file_path).exists(), f'{file_path} does not exist.'

    bands_list = read_bands(file_path)
    print(f'Path : {file_path}')
    print(f'Bands list: {bands_list}')
    #print bands_list using logging
    # logging.info(f'Bands list: {bands_list}')

if __name__ == '__main__':
    main()