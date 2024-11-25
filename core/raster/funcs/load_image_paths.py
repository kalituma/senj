import os
from typing import List, AnyStr, Dict, Callable
from pathlib import Path
from core.util import parse_meta_xml
from core.util.identify import planet_test

from core.raster import ProductType, LOAD_IMAGES_ALLOWED_EXT

def _load_wv_xml_paths(in_path:str) -> List[AnyStr]:
    tmp_meta = parse_meta_xml(in_path, ProductType.WV)
    base_path = Path(in_path).parent
    image_list = [os.path.join(str(base_path), tile_info['FILENAME']) for tile_info in tmp_meta['TILE_INFO']]
    return image_list

def _load_ps_xml_paths(in_path:str) -> List[AnyStr]:
    meta_path = in_path
    file_spec = planet_test(meta_path)
    assert 'analytic' in file_spec, 'analytic band is not found in the input file'
    image_list = [file_spec['analytic']['path']]
    return image_list

def _load_single_image_path(in_path:str) -> List[AnyStr]:
    return [in_path]

XML_HANDLERS:Dict[ProductType, Callable[[AnyStr], List[AnyStr]]] = {
    ProductType.WV: _load_wv_xml_paths,
    ProductType.PS: _load_ps_xml_paths
}

def load_images_paths(in_path:str, product_type:ProductType) -> List[AnyStr]:

    ext = Path(in_path).suffix[1:].lower()
    assert ext in LOAD_IMAGES_ALLOWED_EXT, f'Input file extension({ext}) is not supported for loading images'

    if ext == 'xml':
        handler = XML_HANDLERS.get(product_type)
        if handler is None:
            raise NotImplementedError(f'Product type({product_type}) is not implemented for the input process.')
        image_list = handler(in_path)

    else:
        image_list = _load_single_image_path(in_path)

    for image_path in image_list:
        assert os.path.exists(image_path), f'Image file {image_path} should be exist'

    return image_list