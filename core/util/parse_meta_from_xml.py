from core.util import ProductType
from core.util.meta import parse_worldview, parse_planet
from core.util.identify import safe_test, dim_test, planet_test, worldview_test


def _parse_world_view_meta(path:str) -> dict:
    datafiles = worldview_test(path)
    assert 'metadata' in datafiles, f'metadata file not found in parsing world view data. ({path})'
    meta_path = str(datafiles['metadata']['path'])
    meta_dict = parse_worldview(meta_path)
    return meta_dict

def _parse_planet_meta(path:str) -> dict:
    datafiles = planet_test(path)
    assert 'metadata' in datafiles, f'metadata file not found in parsing world view data. ({path})'


def parse_meta_xml(path:str, product_type:ProductType) -> dict:

    meta_dict = None

    if product_type == ProductType.WV:
        meta_dict = _parse_world_view_meta(path)
    elif product_type == ProductType.PS:
        meta_dict = _parse_planet_meta(path)

    return meta_dict