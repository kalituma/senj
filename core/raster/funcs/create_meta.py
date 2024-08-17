from typing import Union
from pathlib import Path
from esa_snappy import Product
from osgeo.gdal import Dataset
from core.util import ProductType, read_pickle, parse_meta_xml

from core.raster.gpf_module import make_meta_dict

def create_meta_dict(raw:Union[Product, Dataset], product_type:ProductType, path:str) -> Union[dict, None]:

    meta_dict = None

    ext = Path(path).suffix[1:]
    meta_path = path.replace(ext, '.pkl')

    # load if exists
    if Path(meta_path).exists():
        meta_dict = read_pickle(meta_path)
        return meta_dict

    # parse from snap
    if isinstance(raw, Product) and (product_type == ProductType.S2 or product_type == ProductType.S1):
        meta_dict = make_meta_dict(raw)
        return meta_dict

    # parse from xml
    if product_type != ProductType.UNKNOWN:
        meta_dict = parse_meta_xml(path, product_type)
        return meta_dict

    return meta_dict
