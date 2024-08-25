from typing import Union
from pathlib import Path
from esa_snappy import Product
from osgeo.gdal import Dataset
from core.util import ProductType, read_pickle, parse_meta_xml

from core.raster import RasterType
from core.util.gdal import get_image_spec_gdal, get_geo_spec_gdal
from core.util.snap import make_meta_dict_from_product, get_image_spec_gpf, get_geo_spec_gpf

def update_meta_dict(meta_dict:dict, raw:Union[Dataset, Product], module_type:RasterType) -> dict:

    tmp_tile_info = meta_dict['TILE_INFO'][0].copy()
    tmp_band_info = meta_dict['BAND_INFO'].copy()

    if module_type == RasterType.GDAL:
        image_spec = get_image_spec_gdal(raw)
        geo_spec = get_geo_spec_gdal(raw)
    else:
        image_spec = get_image_spec_gpf(raw)
        geo_spec = get_geo_spec_gpf(raw)

    tmp_tile_info['ULCOLOFFSET'] = image_spec['ul_col']
    tmp_tile_info['ULROWOFFSET'] = image_spec['ul_row']
    tmp_tile_info['URCOLOFFSET'] = image_spec['ur_col']
    tmp_tile_info['URROWOFFSET'] = image_spec['ur_row']

    tmp_tile_info['LRCOLOFFSET'] = image_spec['lr_col']
    tmp_tile_info['LRROWOFFSET'] = image_spec['lr_row']
    tmp_tile_info['LLCOLOFFSET'] = image_spec['ll_col']
    tmp_tile_info['LLROWOFFSET'] = image_spec['ll_row']

    tmp_tile_info['ULX'] = tmp_tile_info['ULLON'] = geo_spec['ul_x']
    tmp_tile_info['ULY'] = tmp_tile_info['ULLAT'] = geo_spec['ul_y']
    tmp_tile_info['URX'] = tmp_tile_info['URLON'] = geo_spec['ur_x']
    tmp_tile_info['URY'] = tmp_tile_info['URLAT'] = geo_spec['ur_y']

    tmp_tile_info['LLX'] = tmp_tile_info['LLLON'] = geo_spec['ll_x']
    tmp_tile_info['LLY'] = tmp_tile_info['LLLAT'] = geo_spec['ll_y']
    tmp_tile_info['LRX'] = tmp_tile_info['LRLON'] = geo_spec['lr_x']
    tmp_tile_info['LRY'] = tmp_tile_info['LRLAT'] = geo_spec['lr_y']
    tmp_tile_info['FILENAME'] = ''

    for band_info in tmp_band_info.values():
        band_info['ULLON'] = geo_spec['ul_x']
        band_info['ULLAT'] = geo_spec['ul_y']
        band_info['URLON'] = geo_spec['ur_x']
        band_info['URLAT'] = geo_spec['ur_y']
        band_info['LLLON'] = geo_spec['ll_x']
        band_info['LLLAT'] = geo_spec['ll_y']
        band_info['LRLON'] = geo_spec['lr_x']
        band_info['LRLAT'] = geo_spec['lr_y']

    meta_dict['OR_TILE_FILE_NAMES'] = [tile_info['FILENAME'] for tile_info in meta_dict['TILE_INFO']]
    meta_dict['TILE_INFO'] = [tmp_tile_info]
    meta_dict['BAND_INFO'] = tmp_band_info

    return meta_dict

def create_meta_dict(raw:Union[Product, Dataset], product_type:ProductType, module_type:RasterType, raster_path:str, update_meta_bounds:bool) -> Union[dict, None]:

    meta_dict = None

    ext = Path(raster_path).suffix
    meta_path = raster_path.replace(ext, '.pkl')

    # load if exists
    if Path(meta_path).exists():
        meta_dict = read_pickle(meta_path)
        return meta_dict

    # parse from snap
    if module_type == RasterType.SNAP and (product_type == ProductType.S2 or product_type == ProductType.S1):
        meta_dict = make_meta_dict_from_product(raw,  product_type)
        return meta_dict

    # parse from xml
    if product_type != ProductType.UNKNOWN:
        tif_file_dim = None
        if raw is not None:
            if isinstance(raw, Dataset):
                tif_file_dim = [raw.RasterYSize, raw.RasterXSize]
        meta_dict = parse_meta_xml(raster_path, product_type, tif_file_dim)

        if update_meta_bounds and product_type == ProductType.WV:
            meta_dict = update_meta_dict(meta_dict, raw, module_type)

        return meta_dict

    return meta_dict
