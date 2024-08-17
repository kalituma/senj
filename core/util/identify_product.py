import json
from pathlib import Path
from lxml import etree
from jsonpath_ng.ext import parse

from core.util import ProductType, read_pickle
from core.util.identify import safe_test, dim_test, planet_test, worldview_test

def identify_product(src_path_str:str) -> ProductType:

    src_path = Path(src_path_str)
    if not src_path.exists():
        raise FileNotFoundError(f'{src_path_str} does not exist.')

    ext = src_path.suffix

    # if ext == '.tif':
    #     pkl = src_path.with_suffix('.pkl')
    #     if pkl.exists():
    #         meta_dict = read_pickle(pkl)

    try:
        ################
        ## Sentinel-1,2_SAFE
        mission_id = ''
        data_files = safe_test(src_path_str)
        if 'metadata' in data_files:
            meta = data_files['metadata']['path']
            meta_root = etree.parse(meta).getroot()
            mission_id = meta_root.xpath('//SPACECRAFT_NAME/text()')[0]
        elif 'annotation' in data_files:
            meta = data_files['annotation'][0]['path']
            meta_root = etree.parse(meta).getroot()
            mission_id = str(meta_root.xpath('//missionId/text()')[0])

        if mission_id == 'Sentinel-2A':
            return ProductType.S2
        elif mission_id == 'S1B' or mission_id == 'S1A':
            return ProductType.S1
    except:
        pass

    try:
        ################
        ## Sentinel-1,2_DIM
        mission_id = ''
        data_files = dim_test(src_path_str)
        if 'dim' in data_files:
            meta_root = etree.parse(data_files['dim']).getroot()
            mission_attrs = meta_root.xpath('//MDATTR[@name="SPACECRAFT_NAME"]')
            if len(mission_attrs) > 0:
                mission_id = mission_attrs[0].text
            else:
                mission_attrs = meta_root.xpath('//MDATTR[@name="MISSION"]')
                mission_id = mission_attrs[0].text

        if mission_id == 'Sentinel-2A':
            return ProductType.S2
        elif mission_id == 'SENTINEL-1B':
            return ProductType.S1
    except:
        pass

    try:
        ################
        ## WorldView_TIF
        mission_id = ''
        data_files = worldview_test(src_path_str)
        if 'metadata' in data_files:
            meta = data_files['metadata']['path']
            meta_root = etree.parse(meta).getroot()
            mission_attrs = meta_root.xpath('//SATID/text()')
            if len(mission_attrs) > 0:
                mission_id = mission_attrs[0]
                if mission_id == 'WV02' or mission_id == 'WV03' or mission_id == 'GE01':
                    return ProductType.WV
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
            meta = data_files['metadata']['path']
            meta_root = etree.parse(meta).getroot()
            mission_attrs = meta_root.xpath('//eop:shortName/text()', namespaces=namespaces)

            if len(mission_attrs) > 0:
                if 'PlanetScope' in mission_attrs:
                    return ProductType.PS

        elif 'metadata_json' in data_files:
            meta = data_files['metadata_json']['path']
            meta_dict = json.load(open(meta))
            mission_attrs = parse('$.properties.provider').find(meta_dict)
            if len(mission_attrs) > 0:
                if 'planetscope' in mission_attrs[0].value:
                    return ProductType.PS
    except:
        pass

    return ProductType.UNKNOWN