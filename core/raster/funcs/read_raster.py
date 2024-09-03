import os
from typing import Union, Tuple, List, AnyStr
from pathlib import Path

from core.util import identify_product, parse_meta_xml, read_pickle, get_btoi_from_tif, dict_to_ordered_list
from core.util.identify import planet_test
from core.util.gdal import load_raster_gdal, mosaic_tiles, read_gdal_bands_as_dict
from core.util.snap import load_raster_gpf, mosaic_gpf, rename_bands, read_gpf_bands_as_dict

from core.raster import RasterType, Raster, ProductType
from core.raster.funcs import set_raw_metadict, get_band_name_and_index, create_meta_dict, init_bname_index_in_meta, load_images_paths

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
        path = empty_raster.path = meta_path

    image_paths = load_images_paths(path, product_type)

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
    else:
        raise NotImplementedError(f'Module type({in_module}) is not implemented for the input process.')

    # read band names from tif header first
    btoi_from_header = None
    if Path(path).suffix[1:].lower() == 'tif':
        btoi_from_header = get_btoi_from_tif(path)

    # read and create meta_dict from pkl or xml files intact then update them with new names at tif header
    meta_dict = create_meta_dict(raw, product_type, in_module, path, update_meta_bounds=update_meta_bounds)
    meta_dict = init_bname_index_in_meta(meta_dict, raw, product_type=product_type, module_type=empty_raster.module_type, band_to_index=btoi_from_header)

    # if meta_dict is not None, band_to_index will be None because when 'band_to_index' and 'index_to_band' saved in raster object should refer to metadict first
    if meta_dict:
        btoi_from_header = None

    empty_raster = set_raw_metadict(empty_raster, raw=raw, meta_dict=meta_dict, product_type=product_type)

    if meta_dict is None:
        # meta_dict is not existed, so band_to_index will be used to update band map directly
        empty_raster = empty_raster.update_index_bnames(btoi_from_header)
    else:
        empty_raster.copy_band_map_from_meta()

    # new band names loaded from metadict and tif header should be reflected to product object if snap module is being used
    if empty_raster.module_type == RasterType.SNAP:
        if btoi_from_header is not None:
            empty_raster.raw = rename_bands(empty_raster.raw, band_names=dict_to_ordered_list(btoi_from_header))
        elif meta_dict is not None:
            if 'band_to_index' in meta_dict and 'index_to_band' in meta_dict:
                empty_raster.raw = rename_bands(empty_raster.raw, band_names=dict_to_ordered_list(meta_dict['band_to_index']))

    return empty_raster

def read_band_from_raw(raster:Raster, selected_name_or_id:list[Union[str, int]]=None, add_to_cache=False) -> Raster:

    module_type = raster.module_type

    if selected_name_or_id is None:
        selected_name_or_id = raster.get_band_names()

    bnames, index = get_band_name_and_index(raster, selected_name_or_id)

    if module_type == RasterType.GDAL:
        all_bnames = raster.get_band_names()
        bands, new_selected_bands = read_gdal_bands_as_dict(raster.raw, all_band_names=all_bnames, selected_index=index)
    elif module_type == RasterType.SNAP:
        bands, new_selected_bands = read_gpf_bands_as_dict(raster.raw, bnames)
    else:
        raise NotImplementedError(f'Module type({module_type}) is not implemented for the input process.')

    if add_to_cache:
        if raster.bands == None:
            raster.bands = bands
            # raster.selected_bands = new_selected_bands
        else:
            raster.bands.update(bands)
            # raster.selected_bands = sorted(set(raster.selected_bands + new_selected_bands))
    else:
        raster.bands = bands
        # raster.selected_bands = new_selected_bands

    raster.is_band_cached = True

    return raster