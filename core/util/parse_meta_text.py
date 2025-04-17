from core.util import ProductType, read_json
from core.util.meta import parse_worldview, parse_planet, parse_cas500
from core.util.identify import planet_test, worldview_test, cas500_test, k3_test

meta_parse_funcs = {
    ProductType.WV: parse_worldview,
    ProductType.PS: parse_planet,
    ProductType.CA: parse_cas500,
    ProductType.K3: parse_cas500
}

datafile_funcs = {
    ProductType.WV: worldview_test,
    ProductType.PS: planet_test,
    ProductType.CA: cas500_test,
    ProductType.K3: k3_test
}

def parse_meta_xml(path:str, product_type:ProductType, tif_file_dim:list=None) -> dict:

    assert product_type in meta_parse_funcs, f'product type {product_type} is not supported for parsing meta xml'
    datafiles = datafile_funcs[product_type](path)
    assert 'metadata' in datafiles, f'metadata file not found in parsing {product_type} data. ({path})'
    meta_path = str(datafiles['metadata']['path'])
    meta_dict = meta_parse_funcs[product_type](meta_path)
    assert len(meta_dict) > 0, f'failed to parse meta xml from {meta_path}'

    if product_type == ProductType.WV:
        if tif_file_dim:
            assert int(meta_dict['NUMROWS']) == tif_file_dim[0], f'tif file dimension does not match with meta xml. {meta_dict["NUMROWS"]} != {tif_file_dim[0]}'
            assert int(meta_dict['NUMCOLUMNS']) == tif_file_dim[1], f'tif file dimension does not match with meta xml. {meta_dict["NUMCOLUMNS"]} != {tif_file_dim[1]}'
        
    return meta_dict

def parse_meta_capella(meta_path:str, extended_meta_path:str) -> dict:
    
    meta_dict = {}
    tmp_meta_dict = read_json(meta_path)
    tmp_extended_meta_dict = read_json(extended_meta_path)
    
    meta_dict['meta'] = tmp_meta_dict
    meta_dict['extended_meta'] = tmp_extended_meta_dict
    
    return meta_dict