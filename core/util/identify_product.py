import json
from pathlib import Path
from lxml import etree

from core.util import S1_MISSION_PATTERN, S2_MISSION_PATTERN
from core.util import ProductType, read_pickle, query_dict
from core.util.identify import safe_test, dim_test, planet_test, worldview_test

def check_product_type_using_meta(meta_dict: dict) -> ProductType:
    if meta_dict is None or len(meta_dict) == 0:
        return ProductType.UNKNOWN

    try:
        if len(query_dict(S1_MISSION_PATTERN, target_dict=meta_dict)) > 0:
            found_values = query_dict(S1_MISSION_PATTERN, target_dict=meta_dict)
            if 'sentinel-1' in found_values[0].lower():
                return ProductType.S1
            else:
                return ProductType.UNKNOWN
        elif len(query_dict(S2_MISSION_PATTERN, target_dict=meta_dict)) > 0:
            found_values = query_dict(S2_MISSION_PATTERN, target_dict=meta_dict)
            if 'sentinel-2' in found_values[0].lower():
                return ProductType.S2
            else:
                return ProductType.UNKNOWN
        else:
            return ProductType.UNKNOWN
    except:
        return ProductType.UNKNOWN

def identify_product(src_path_str:str) -> tuple[ProductType,str]:

    src_path = Path(src_path_str)
    if not src_path.exists():
        raise FileNotFoundError(f'{src_path_str} does not exist.')

    meta_path = ''
    ext = src_path.suffix

    if ext == '.tif':
        pkl = src_path.with_suffix('.pkl')
        if pkl.exists():
            meta_dict = read_pickle(pkl)
            return check_product_type_using_meta(meta_dict), str(pkl)

    try:
        ################
        ## Sentinel-1,2_SAFE
        mission_id = ''
        meta_path = ''
        data_files = safe_test(safe_dir=src_path_str)
        if 'metadata' in data_files:
            meta_path = data_files['metadata']['path']
            meta_root = etree.parse(meta_path).getroot()
            mission_id = meta_root.xpath('//SPACECRAFT_NAME/text()')[0]
        elif 'annotation' in data_files:
            meta_path = data_files['annotation'][0]['path']
            meta_root = etree.parse(meta_path).getroot()
            mission_id = str(meta_root.xpath('//missionId/text()')[0])

        if mission_id == 'Sentinel-2A':
            return ProductType.S2, meta_path
        elif mission_id == 'S1B' or mission_id == 'S1A':
            return ProductType.S1, meta_path
    except:
        pass

    try:
        ################
        ## Sentinel-1,2_DIM
        mission_id = ''
        data_files = dim_test(dim_or_data_path=src_path_str)
        if 'dim' in data_files:
            meta_root = etree.parse(data_files['dim']).getroot()
            mission_attrs = meta_root.xpath('//MDATTR[@name="SPACECRAFT_NAME"]')
            if len(mission_attrs) > 0:
                mission_id = mission_attrs[0].text
            else:
                mission_attrs = meta_root.xpath('//MDATTR[@name="MISSION"]')
                mission_id = mission_attrs[0].text

        if mission_id == 'Sentinel-2A':
            return ProductType.S2, data_files['dim']
        elif mission_id == 'SENTINEL-1B':
            return ProductType.S1, data_files['dim']
    except:
        pass

    try:
        ################
        ## WorldView_TIF
        mission_id = ''
        data_files = worldview_test(tif_or_xml_path=src_path_str)
        if 'metadata' in data_files:
            meta_path = data_files['metadata']['path']
            meta_root = etree.parse(meta_path).getroot()
            mission_attrs = meta_root.xpath('//SATID/text()')
            if len(mission_attrs) > 0:
                mission_id = mission_attrs[0]
                if mission_id == 'WV02' or mission_id == 'WV03' or mission_id == 'GE01':
                    return ProductType.WV, str(meta_path)
    except:
        pass

    try:
        ################
        ## PlanetScope
        mission_id = ''
        data_files = planet_test(src_path_str)
        if 'metadata' in data_files:
            namespaces = {
                'eop': 'http://earth.esa.int/eop',
            }
            meta_path = data_files['metadata']['path']
            meta_root = etree.parse(meta_path).getroot()
            mission_attrs = meta_root.xpath('//eop:shortName/text()', namespaces=namespaces)

            if len(mission_attrs) > 0:
                if 'PlanetScope' in mission_attrs:
                    return ProductType.PS, meta_path
        elif 'metadata_json' in data_files:
            meta_path = data_files['metadata_json']['path']
            meta_dict = json.load(open(meta_path))
            mission_attrs_values = query_dict('$.properties.provider', meta_dict)
            if len(mission_attrs_values) > 0:
                if 'planetscope' in mission_attrs_values[0]:
                    return ProductType.PS, meta_path
    except:
        pass

    # todo: add warning message to alert that meta_path is not found
    return ProductType.UNKNOWN, meta_path