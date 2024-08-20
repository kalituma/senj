from typing import Union

from core.util import ProductType
from core.util.meta import parse_worldview, parse_planet
from core.util.identify import planet_test, worldview_test

meta_parse_funcs = {
    ProductType.WV: parse_worldview,
    ProductType.PS: parse_planet
}

datafile_funcs = {
    ProductType.WV: worldview_test,
    ProductType.PS: planet_test
}

def parse_meta_xml(path:str, product_type:ProductType, tif_file_dim:list=None) -> dict:

    assert product_type in meta_parse_funcs, f'product type {product_type} is not supported for parsing meta xml'
    datafiles = datafile_funcs[product_type](path)
    assert 'metadata' in datafiles, f'metadata file not found in parsing world view data. ({path})'
    meta_path = str(datafiles['metadata']['path'])
    meta_dict = meta_parse_funcs[product_type](meta_path)
    assert len(meta_dict) > 0, f'failed to parse meta xml from {meta_path}'

    if product_type == ProductType.WV:
        if tif_file_dim:
            assert int(meta_dict['NUMROWS']) == tif_file_dim[0], f'tif file dimension does not match with meta xml. {meta_dict["NUMROWS"]} != {tif_file_dim[0]}'
            assert int(meta_dict['NUMCOLUMNS']) == tif_file_dim[1], f'tif file dimension does not match with meta xml. {meta_dict["NUMCOLUMNS"]} != {tif_file_dim[1]}'
        
    return meta_dict
