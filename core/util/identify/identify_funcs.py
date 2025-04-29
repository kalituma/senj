from typing import Callable, Tuple
import json
from lxml import etree
from netCDF4 import Dataset
import functools

from core.util import ProductType, query_dict, read_json
from core.util import S1_MISSION_PATTERN, S2_MISSION_PATTERN, PS_MISSION_PATTERN, WV_MISSION_PATTERN
from core.util import ProductType, query_dict, read_json
from core.util.gdal import read_single
from core.util.identify import safe_test, dim_test, planet_test, worldview_test, capella_test, cas500_test, k3_test

def check_product_type_using_meta(meta_dict: dict) -> ProductType:
    if meta_dict is None or len(meta_dict) == 0:
        return ProductType.UNKNOWN

    try:
        if len(query_dict(S1_MISSION_PATTERN, target_dict=meta_dict)) > 0:
            found_values = query_dict(S1_MISSION_PATTERN, target_dict=meta_dict)
            if 'sentinel-1' in found_values[0].lower():
                return ProductType.S1
        elif len(query_dict(S2_MISSION_PATTERN, target_dict=meta_dict)) > 0:
            found_values = query_dict(S2_MISSION_PATTERN, target_dict=meta_dict)
            if 'sentinel-2' in found_values[0].lower():
                return ProductType.S2
        elif len(query_dict(PS_MISSION_PATTERN, target_dict=meta_dict)) > 0:
            found_values = query_dict(PS_MISSION_PATTERN, target_dict=meta_dict)
            if 'planetscope' in found_values[0].lower():
                return ProductType.PS
        elif len(query_dict(WV_MISSION_PATTERN, target_dict=meta_dict)) > 0:
            found_values = query_dict(WV_MISSION_PATTERN, target_dict=meta_dict)
            if 'geoeye' in found_values[0].lower() or 'worldview' in found_values[0].lower():
                return ProductType.WV

        return ProductType.UNKNOWN
    except:
        return ProductType.UNKNOWN

def with_unknown_product_fallback(func: Callable) -> Callable:
    
    @functools.wraps(func)
    def wrapper(src_path_str: str) -> Tuple[ProductType, str]:
        try:
            result = func(src_path_str) 
            if result is None:
                raise ValueError(f"Unknown product type for file: {src_path_str}")
            return result
        except Exception as e:
            if isinstance(e, ValueError) and "Unknown product type" in str(e):
                raise
            raise ValueError(f"Unknown product type for file: {src_path_str}")
    
    return wrapper

@with_unknown_product_fallback
def identify_safe(src_path_str:str):
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

    if mission_id == 'Sentinel-2A' or mission_id == 'Sentinel-2B':
        return ProductType.S2, meta_path
    elif mission_id == 'S1B' or mission_id == 'S1A':
        return ProductType.S1, meta_path

@with_unknown_product_fallback
def identify_dim(src_path_str:str):
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

@with_unknown_product_fallback
def identify_wv(src_path_str:str):
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

@with_unknown_product_fallback
def identify_capella(src_path_str:str):    
    data_files = capella_test(src_path_str)
    if 'metadata' in data_files:
        meta_path = data_files['metadata']['path']        
        meta_dict = read_json(meta_path)
        platform_name = query_dict('$.properties.platform', meta_dict)
        if len(platform_name) > 0:
            if 'capella' in platform_name[0]:
                return ProductType.CP, str(meta_path)

@with_unknown_product_fallback
def identify_cas500(src_path_str:str):
    data_files = cas500_test(src_path_str)
    if 'metadata' in data_files:
        return ProductType.CA, str(data_files['metadata']['path'])

@with_unknown_product_fallback
def identify_k3(src_path_str:str):
    data_files = k3_test(src_path_str)
    if 'metadata' in data_files:
        return ProductType.K3, str(data_files['metadata']['path'])

@with_unknown_product_fallback
def identify_ps(src_path_str:str):
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

@with_unknown_product_fallback
def identify_nc(src_path_str:str):
    nc_file = Dataset(src_path_str, 'r')

    keys = ['instrument', 'title']

    for key in keys:    
        value = getattr(nc_file, key , None)
        if value is not None:            
            if 'GK2B GOCI-II Level-2 Data' in value:
                if 'geophysical_data' in nc_file.groups:
                    if 'Rrs' in nc_file['geophysical_data'].groups:
                        return ProductType.GOCI_AC, src_path_str
                    if 'CDOM' in nc_file['geophysical_data'].variables:
                        return ProductType.GOCI_CDOM, src_path_str
            elif 'SMAP' in value:
                return ProductType.SMAP, src_path_str
            elif '해수면온도' in value:
                algorithm = getattr(nc_file, 'algorithm', None)
                if algorithm:
                    if 'SST' in algorithm:
                        return ProductType.KHOA_SST, src_path_str
            elif 'GK-2A' in value:
                return ProductType.GK2A, src_path_str

@with_unknown_product_fallback
def identify_gb(src_path_str:str):
    
    ds = read_single(src_path_str)
    band_desc = ds.GetRasterBand(1).GetMetadataItem("GRIB_IDS")

    if 'Seoul' in band_desc and 'Analysis_and_forecast' in band_desc:
        return ProductType.LDAPS, src_path_str
    
