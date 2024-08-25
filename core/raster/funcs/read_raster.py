import os
from typing import Union, Tuple, List, AnyStr
from pathlib import Path
from core.util import identify_product, parse_meta_xml, read_pickle
from core.util.identify import planet_test

from core.raster import RasterType, Raster, ProductType
from core.util.gdal import load_raster_gdal, mosaic_tiles
from core.util.snap import load_raster_gpf, mosaic_gpf, rename_bands

from core.raster.funcs import read_gdal_bands_as_dict, read_gpf_bands_as_dict, set_raw_metadict, \
    get_band_name_and_index, create_meta_dict, create_band_name_idx

def load_images_paths_and_bnames(in_path:str, product_type) -> Tuple[List[AnyStr], List[AnyStr]]:
    ext = Path(in_path).suffix.lower()

    loaded_bnames = None
    if ext == '.xml':
        if product_type == ProductType.WV:
            tmp_meta = parse_meta_xml(in_path, product_type)
            band_idx = [item['index'] for key, item in tmp_meta['BAND_INFO'].items()]
            loaded_bnames = [key for key, item in tmp_meta['BAND_INFO'].items()]
            loaded_bnames = [x for _, x in sorted(zip(band_idx, loaded_bnames))]

            base_path = Path(in_path).parent
            image_list = [os.path.join(str(base_path), tile_info['FILENAME']) for tile_info in tmp_meta['TILE_INFO']]

        elif product_type == ProductType.PS:
            meta_path = in_path
            file_spec = planet_test(meta_path)
            assert 'analytic' in file_spec, 'analytic band is not found in the input file'
            image_list = [file_spec['analytic']['path']]
        else:
            raise NotImplementedError(f'Product type({product_type}) is not implemented for the input process.')
    else:
        if ext == '.tif':
            meta_path = in_path.replace('.tif', '.pkl')
            if os.path.exists(meta_path):
                tmp_meta = read_pickle(meta_path)
                if 'band_to_index' in tmp_meta and 'index_to_band' in tmp_meta:
                    band_idx = list(tmp_meta['index_to_band'].keys())
                    loaded_bnames = list(tmp_meta['index_to_band'].values())
                    loaded_bnames = [x for _, x in sorted(zip(band_idx, loaded_bnames))]
        image_list = [in_path]

    for image_path in image_list:
        assert os.path.exists(image_path), f'Image file {image_path} should be exist'

    return image_list, loaded_bnames

def load_raster(empty_raster:Raster, in_module:RasterType) -> Raster:

    path = empty_raster.path
    empty_raster.module_type = in_module

    product_type, meta_path = identify_product(path)

    if product_type == ProductType.WV: # to merge tiles for WorldView, in_path should be the xml file
        empty_raster.path = meta_path
        path = meta_path

    image_paths, bnames = load_images_paths_and_bnames(path, product_type)
    update_meta_bounds = False
    if empty_raster.module_type == RasterType.GDAL:

        if len(image_paths) > 1:
            raw = mosaic_tiles(image_paths)
            update_meta_bounds = True
        else:
            datasets = load_raster_gdal(image_paths)
            raw = datasets[0]

    elif empty_raster.module_type == RasterType.SNAP:
        datasets = load_raster_gpf(image_paths)
        if len(datasets) > 1:
            raw = mosaic_gpf(datasets)
            update_meta_bounds = True
        else:
            raw = datasets[0]
        if bnames:
            raw = rename_bands(raw, bnames)
    else:
        raise NotImplementedError(f'Module type({in_module}) is not implemented for the input process.')

    meta_dict = create_meta_dict(raw, product_type, in_module, path, update_meta_bounds=update_meta_bounds)
    if meta_dict:
        meta_dict = create_band_name_idx(meta_dict, raw, product_type=product_type, module_type=empty_raster.module_type)

    empty_raster = set_raw_metadict(empty_raster, raw=raw, meta_dict=meta_dict, product_type=product_type)
    empty_raster = empty_raster.update_index_bnames()

    return empty_raster

def read_band_from_raw(raster:Raster, selected_band:list[Union[str, int]]=None) -> Raster:

    module_type = raster.module_type

    if selected_band is None:
        selected_band = raster.get_band_names()

    if module_type == RasterType.GDAL:
        _, index = get_band_name_and_index(raster, selected_band)
        raster.bands, raster.selected_bands = read_gdal_bands_as_dict(raster.raw, band_names=selected_band, selected_index=index)
    elif module_type == RasterType.SNAP:
        raster.bands, raster.selected_bands = read_gpf_bands_as_dict(raster.raw, selected_band)
    else:
        raise NotImplementedError(f'Module type({module_type}) is not implemented for the input process.')

    raster.is_band_cached = True

    return raster