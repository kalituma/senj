import os
from typing import List, AnyStr
from pathlib import Path
from core.util import parse_meta_xml
from core.util.identify import planet_test

from core.raster import ProductType, LOAD_IMAGES_ALLOWED_EXT

def load_images_paths(in_path:str, product_type:ProductType) -> List[AnyStr]:

    ext = Path(in_path).suffix[1:].lower()
    assert ext in LOAD_IMAGES_ALLOWED_EXT, f'Input file extension({ext}) is not supported for loading images'

    if ext == 'xml':
        if product_type == ProductType.WV:
            tmp_meta = parse_meta_xml(in_path, product_type)

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
        image_list = [in_path]

    for image_path in image_list:
        assert os.path.exists(image_path), f'Image file {image_path} should be exist'

    return image_list