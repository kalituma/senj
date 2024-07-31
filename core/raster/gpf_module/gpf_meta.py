from typing import Union

import numpy as np
import copy
import dateutil.parser
from jsonpath_ng.ext import parse

from esa_snappy import jpy
from esa_snappy import Product

from core.util import tiles_interp, grid_extend, distance_se, projection_geo
from core.raster.gdal_module import warp_to
from core.raster.gpf_module.meta_func import get_metadata_recursive, get_metadata_value, grid_geom, build_meta_dict, set_meta_recursive

def get_polarization(meta_dict:dict) -> Union[list[str], None]:
    pols = list(set(found.value for found in parse('$..*[polarization]').find(meta_dict)))

    if len(pols) == 0:
        return None

    return pols

def make_meta_dict(product:Product):
    meta_dict = build_meta_dict(product.getMetadataRoot())
    meta_dict['band_to_index'] = {band: i + 1 for i, band in enumerate(product.getBandNames())}
    meta_dict['index_to_band'] = {i + 1: band for i, band in enumerate(product.getBandNames())}
    return meta_dict

def set_meta_to_product(product:Product, meta_dict:dict):

    metadata_element = jpy.get_type('org.esa.snap.core.datamodel.MetadataElement')

    meta_root = product.getMetadataRoot()
    for key, _ in meta_dict.items():
        if key != 'band_to_index' and key != 'index_to_band':
            if not meta_root.containsElement(key):
                sub_elem = set_meta_recursive(metadata_element(key), meta_dict[key])
                meta_root.addElement(sub_elem)

    return product

def read_grid_angle_meta_from_product(product:Product) -> dict:

    # read tileid, datastripid, sensing time, horizontal and vertical cs name, horizontal and vertical cs code
    meta_root = product.getMetadataRoot()
    granule_par_tag = meta_root.getElement('Granules').getElementAt(0).getName()

    granule_meta = {}

    tile_id = get_metadata_value(meta_root, f'Granules/{granule_par_tag}/General_Info/TILE_ID')
    granule_meta['TILE_ID'] = tile_id
    datastrip_id = get_metadata_value(meta_root, f'Granules/{granule_par_tag}/General_Info/DATASTRIP_ID')
    granule_meta['DATASTRIP_ID'] = datastrip_id
    sensing_time = get_metadata_value(meta_root, f'Granules/{granule_par_tag}/General_Info/SENSING_TIME')
    granule_meta['SENSING_TIME'] = sensing_time
    horizontal_cs_name = get_metadata_value(meta_root,
                                            f'Granules/{granule_par_tag}/Geometric_Info/Tile_GeoCoding/HORIZONTAL_CS_NAME')
    granule_meta['HORIZONTAL_CS_NAME'] = horizontal_cs_name
    horizontal_cs_code = get_metadata_value(meta_root,
                                            f'Granules/{granule_par_tag}/Geometric_Info/Tile_GeoCoding/HORIZONTAL_CS_CODE')
    granule_meta['HORIZONTAL_CS_CODE'] = horizontal_cs_code

    grids = _parse_tile_geocoding(meta_root, granule_par_tag)
    granule_meta['GRIDS'] = grids

    sun, view, view_det = _parse_tile_angle(meta_root, granule_par_tag)
    granule_meta['SUN'] = sun
    granule_meta['VIEW'] = view
    granule_meta['VIEW_DET'] = view_det
    granule_meta['GRANULE_PARENT'] = granule_par_tag

    return granule_meta

def make_gattr(product:Product):

    input_file = str(product.getFileLocation())

    product_meta_root = product.getMetadataRoot()
    gr_meta = read_grid_angle_meta_from_product(product_meta_root)

    gr_meta['CUR_GRIDS'] = band_size_per_res(product)

    meta, band_data = metadata_scene(product)
    granule = granule_info(product_meta_root)
    sensor_name = find_sensor_name(meta['SPACECRAFT_NAME'])

    if meta['PROCESSING_LEVEL'] != 'Level-1C':
        raise ValueError(f'Processing of {input_file} Sentinel-2 {meta["PROCESSING_LEVEL"]} data not supported')

    dtime = dateutil.parser.parse(gr_meta['SENSING_TIME'])
    doy = dtime.strftime('%j')
    se_distance = distance_se(doy)
    isodate = dtime.isoformat()

    mgrs_tile = gr_meta['TILE_ID'].split('_')[-2]

    ## scene average geometry
    sza = gr_meta['SUN']['Mean_Zenith']
    saa = gr_meta['SUN']['Mean_Azimuth']
    vza = np.nanmean(gr_meta['VIEW']['Average_View_Zenith'])
    vaa = np.nanmean(gr_meta['VIEW']['Average_View_Azimuth'])
    raa = np.abs(saa - vaa)
    while raa > 180:
        raa = np.abs(360 - raa)

    if 'RADIO_ADD_OFFSET' in band_data:
        for Bn in band_data['RADIO_ADD_OFFSET']:
            band_data['RADIO_ADD_OFFSET'][Bn] = float(band_data['RADIO_ADD_OFFSET'][Bn])

    quant = float(meta['QUANTIFICATION_VALUE'])
    nodata = int(meta['NODATA'])

    gatts = {
        'sensor': sensor_name, 'isodate': isodate,
        'sza': sza, 'vza': vza, 'raa': raa, 'vaa': vaa, 'saa': saa, 'se_distance': se_distance,
        'mus': np.cos(sza * (np.pi / 180.)), 'granule': granule, 'mgrs_tile': mgrs_tile,
        'gr_meta' : gr_meta, 'acolite_file_type': 'L1R', 'band_data': band_data, 'quant': quant, 'nodata': nodata
    }

    return gatts



def get_src_param(meta, geom_res, prefix=""):
    src_params = {}
    src_params['ydim'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['NROWS']
    src_params['xdim'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['NCOLS']
    src_params['ul_x'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['ULX']
    src_params['ul_y'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['ULY']
    src_params['epsg'] = int(meta['HORIZONTAL_CS_CODE'].split(':')[1])
    src_params['pixel_size'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['RESOLUTION']

    return src_params

def copy_dct_to_atts(dct, atts, prefix=''):
    atts[f'{prefix}scene_xrange'] = dct['xrange']
    atts[f'{prefix}scene_yrange'] = dct['yrange']
    atts[f'{prefix}scene_proj4_string'] = dct['proj4_string']
    atts[f'{prefix}scene_pixel_size'] = dct['pixel_size']
    atts[f'{prefix}scene_dims'] = dct['dimensions']
    if 'zone' in dct:
        atts[f'{prefix}scene_zone'] = dct['zone']
    return atts

def find_sensor_name(spacecraft_name):
    if spacecraft_name == 'Sentinel-2A':
        return 'S2A_MSI'
    elif spacecraft_name == 'Sentinel-2B':
        return 'S2B_MSI'
    else:
        return None

def get_index_str_to_band_str() -> dict:

    return {'0': 'B1', '1': 'B2', '2': 'B3', '3': 'B4', '4': 'B5', '5': 'B6', '6': 'B7',
                             '7': 'B8', '8': 'B8A', '9': 'B9', '10': 'B10', '11': 'B11', '12': 'B12'}

def granule_info(meta_root):

    granule_uri = 'Level-1C_User_Product/General_Info/Product_Info/Product_Organisation/Granule_List/Granule'
    granule_tag = 'IMAGE_FILE'

    granule_par = get_metadata_recursive(meta_root, granule_uri)

    for granule in granule_par.getAttributes():
        if granule.getName() != granule_tag:
            continue
        image_path = granule.getData().getElemString()
        # extract granule name
        granule_dir = image_path.split('/')
        granule_idx = 0
        for i, d in enumerate(granule_dir):
            if d == 'GRANULE':
                granule_idx = i+1
                break

        return granule_dir[granule_idx]

def get_band_info_meta(meta_dict:dict):

    banddata = {}
    banddata['BandNames'] = {}
    banddata['Resolution'] = {}
    banddata['Wavelength'] = {}
    banddata['RSR'] = {}

    find_meta_dict = lambda x: [field.value for field in parse(x).find(meta_dict)]

    img_characteristics_uri = '$.Level-1C_User_Product.General_Info.Product_Image_Characteristics'
    reflectance_conv_uri = '$.Level-1C_User_Product.General_Info.Product_Image_Characteristics.Reflectance_Conversion'

    spectral_uri = f'{img_characteristics_uri}.Spectral_Information_List.Spectral_Information'
    spec_info_list = find_meta_dict(spectral_uri)[0]

    for spec_info in spec_info_list:
        bandi = spec_info['bandId']
        phy_band = spec_info['physicalBand']
        res = spec_info['RESOLUTION']
        banddata['BandNames'][bandi] = phy_band
        banddata['Resolution'][phy_band] = res
        banddata['Wavelength'][phy_band] = {key: float(value) for key, value in spec_info['Wavelength'].items()}

        step = spec_info['Spectral_Response']['STEP']
        values = spec_info['Spectral_Response']['VALUES']
        rsr = [float(rs) for rs in values.split(' ')]

        wave = np.linspace(
            float(banddata['Wavelength'][phy_band]['MIN']), \
            float(banddata['Wavelength'][phy_band]['MAX']), \
            int((float(banddata['Wavelength'][phy_band]['MAX']) - float(banddata['Wavelength'][phy_band]['MIN'])) / float(step) + 1)
        )

        banddata['RSR'][phy_band] = {'response': rsr, 'wave': wave}

    if len(banddata['BandNames']) == 0:
        banddata['BandNames'] = get_index_str_to_band_str()

    if 'F0' not in banddata:
        banddata['F0'] = {}

    f_uri = f'{reflectance_conv_uri}.Solar_Irradiance_List.SOLAR_IRRADIANCE'
    f0_list = find_meta_dict(f_uri)[0]

    for bi, f in enumerate(f0_list):
        band = banddata['BandNames'][f'{bi}']
        banddata['F0'][band] = float(f)

    phy_tag = 'PHYSICAL_GAINS'
    phy_gain_uri = f'{img_characteristics_uri}.{phy_tag}'
    phy_gain_list = find_meta_dict(phy_gain_uri)[0]
    for bi, t in enumerate(phy_gain_list):
        if phy_tag not in banddata:
            banddata[phy_tag] = {}
        band = banddata['BandNames'][f'{bi}']
        banddata[phy_tag][band] = float(t)

    rad_tag = 'RADIO_ADD_OFFSET'
    rad_uri = f'{img_characteristics_uri}.Radiometric_Offset_List.{rad_tag}'
    rad_list = find_meta_dict(rad_uri)[0]
    for bi, t in enumerate(rad_list):
        if rad_tag not in banddata:
            banddata[rad_tag] = {}
        band = banddata['BandNames'][f'{bi}']
        banddata[rad_tag][band] = float(t)

    return banddata

def get_band_info_meta_from_product(product:Product) -> dict:

    meta_root = product.getMetadataRoot()

    banddata = {}
    banddata['BandNames'] = {}
    banddata['Resolution'] = {}
    banddata['Wavelength'] = {}
    banddata['RSR'] = {}

    img_characteristics_uri = 'Level-1C_User_Product/General_Info/Product_Image_Characteristics'
    spectral_uri = f'{img_characteristics_uri}/Spectral_Information_List'

    spectral_subs = 'Spectral_Information'
    spectral_par = get_metadata_recursive(meta_root, spectral_uri)

    for spectral in spectral_par.getElements():
        if spectral.getName() != spectral_subs:
            continue
        bandi = spectral.getAttribute('bandId').getData().getElemString()
        band = spectral.getAttribute('physicalBand').getData().getElemString()
        res = spectral.getAttribute('RESOLUTION').getData().getElemString()
        banddata['BandNames'][bandi] = band
        banddata['Resolution'][band] = res
        banddata['Wavelength'][band] = {tag: float(get_metadata_value(spectral, f'Wavelength/{tag}')) for tag in
                                        ['CENTRAL', 'MIN', 'MAX']}

        step = get_metadata_value(spectral, 'Spectral_Response/STEP')
        values = get_metadata_value(spectral, 'Spectral_Response/VALUES')
        rsr = [float(rs) for rs in values.split(' ')]

        wave = np.linspace(
            float(banddata['Wavelength'][band]['MIN']), \
            float(banddata['Wavelength'][band]['MAX']), \
            int((float(banddata['Wavelength'][band]['MAX']) - float(banddata['Wavelength'][band]['MIN'])) / float(
                step) + 1)
        )

        banddata['RSR'][band] = {'response': rsr, 'wave': wave}

    if len(banddata['BandNames']) == 0:
        banddata['BandNames'] = get_index_str_to_band_str()

    f_uri_root = 'Level-1C_User_Product/General_Info/Product_Image_Characteristics/Reflectance_Conversion'
    f_uri = f'{f_uri_root}/Solar_Irradiance_List'

    if 'F0' not in banddata: banddata['F0'] = {}

    for bi, f in enumerate(get_metadata_recursive(meta_root, f_uri).getAttributes()):
        band = banddata['BandNames'][f'{bi}']
        banddata['F0'][band] = float(f.getData().getElemString())

    phy_uri = f'{img_characteristics_uri}'
    phy_tag = 'PHYSICAL_GAINS'
    cnt = 0
    for t in get_metadata_recursive(meta_root, phy_uri).getAttributes():
        if phy_tag not in banddata: banddata[phy_tag] = {}
        if t.getName() != phy_tag:
            continue
        band = banddata['BandNames'][f'{cnt}']
        banddata[phy_tag][band] = float(t.getData().getElemString())
        cnt += 1

    rad_uri = f'{img_characteristics_uri}/Radiometric_Offset_List'
    rad_tag = 'RADIO_ADD_OFFSET'
    for bi, t in enumerate(get_metadata_recursive(meta_root, rad_uri).getAttributes()):
        if rad_tag not in banddata: banddata[rad_tag] = {}
        if t.getName() != rad_tag:
            continue
        band = banddata['BandNames'][f'{bi}']
        banddata[rad_tag][band] = float(t.getData().getElemString())

    return banddata

def get_product_info_meta(meta_dict:dict) -> dict:

    product_info_uri = [
        '$.Level-1C_User_Product.General_Info.Product_Info',
        '$.Level-1C_User_Product.General_Info.Product_Info.Datatake',
        '$.Level-1C_User_Product.General_Info.Product_Info.Query_Options',
        '$.Level-1C_User_Product.General_Info.Product_Image_Characteristics',
        '$.Level-1C_User_Product.General_Info.Product_Image_Characteristics.Reflectance_Conversion'
    ]

    product_info_tags = [
        ['PRODUCT_START_TIME', 'PRODUCT_STOP_TIME', 'PRODUCT_URI', 'PROCESSING_LEVEL', 'PRODUCT_TYPE',
         'PROCESSING_BASELINE', 'GENERATION_TIME'],
        ['SPACECRAFT_NAME', 'DATATAKE_SENSING_START', 'SENSING_ORBIT_NUMBER', 'SENSING_ORBIT_DIRECTION'],
        ['PRODUCT_FORMAT'],
        ['QUANTIFICATION_VALUE'],
        ['U']
    ]

    reflectance_metadata = {}
    find_meta_dict = lambda x: [field.value for field in parse(x).find(meta_dict)]

    for i, uri in enumerate(product_info_uri):
        info_node = find_meta_dict(uri)[0]
        for attr_tag in product_info_tags[i]:
            value = info_node[attr_tag]
            reflectance_metadata[attr_tag] = value

    # special values
    special_uri = product_info_uri[3]
    special_tag = 'Special_Values'

    special_nodes = find_meta_dict(special_uri)[0][special_tag]
    for special_node in special_nodes:
        reflectance_metadata[special_node['SPECIAL_VALUE_TEXT']] = special_node['SPECIAL_VALUE_INDEX']

    return reflectance_metadata

def get_reflectance_meta_from_product(product:Product) -> dict:

    product_info_uri = ['Level-1C_User_Product/General_Info/Product_Info',
                        'Level-1C_User_Product/General_Info/Product_Info/Datatake',
                        'Level-1C_User_Product/General_Info/Product_Info/Query_Options',
                        'Level-1C_User_Product/General_Info/Product_Image_Characteristics',
                        'Level-1C_User_Product/General_Info/Product_Image_Characteristics/Reflectance_Conversion']

    product_info_tags = [
        ['PRODUCT_START_TIME', 'PRODUCT_STOP_TIME', 'PRODUCT_URI', 'PROCESSING_LEVEL', 'PRODUCT_TYPE',
         'PROCESSING_BASELINE', 'GENERATION_TIME'],
        ['SPACECRAFT_NAME', 'DATATAKE_SENSING_START', 'SENSING_ORBIT_NUMBER', 'SENSING_ORBIT_DIRECTION'],
        ['PRODUCT_FORMAT'],
        ['QUANTIFICATION_VALUE'],
        ['U']
    ]
    # 'BOA_QUANTIFICATION_VALUE', 'AOT_QUANTIFICATION_VALUE', 'WVP_QUANTIFICATION_VALUE'  ## sen2cor

    meta_root = product.getMetadataRoot()

    reflectance_meta = {}

    for i, uri in enumerate(product_info_uri):
        for attr_tag in product_info_tags[i]:
            child_uri = f'{uri}/{attr_tag}'
            value = get_metadata_value(meta_root, child_uri)
            reflectance_meta[attr_tag] = value

    special_uri = product_info_uri[3]
    special_tag = 'Special_Values'

    special_par = get_metadata_recursive(meta_root, f'{special_uri}')
    for special in special_par.getElements():
        if special.getName() != special_tag:
            continue
        fill = special.getAttribute('SPECIAL_VALUE_TEXT').getData().getElemString()
        fill_value = special.getAttribute('SPECIAL_VALUE_INDEX').getData().getElemString()
        reflectance_meta[fill] = fill_value

    return reflectance_meta

def _parse_tile_geocoding(meta_root, granule_par_tag):
    grids = {'10': {}, '20': {}, '60': {}}
    # res
    tile_geocoding_elem = get_metadata_recursive(meta_root,
                                                 f'Granules/{granule_par_tag}/Geometric_Info/Tile_GeoCoding')
    for i, elem in enumerate(tile_geocoding_elem.getElements()):

        res = elem.getAttribute('resolution').getData().getElemString()
        grids[res]['RESOLUTION'] = float(res)

        if elem.getName() == 'Size':
            tags = ['NROWS', 'NCOLS']
        else:
            tags = ['ULX', 'ULY', 'XDIM', 'YDIM']

        for tag in tags:
            value = elem.getAttribute(tag).getData().getElemString()
            grids[res][tag] = float(value)

    return grids

def _parse_tile_angle(meta_root, granule_par_tag):

    root_tags = f'Granules/{granule_par_tag}/Geometric_Info/Tile_Angles'
    sub_tags = ['Sun_Angles_Grid', 'Mean_Sun_Angle', 'Viewing_Incidence_Angles_Grids']
    angle_types = ['Zenith', 'Azimuth']

    sun = {}
    view = {}
    view_det = {}
    elem = get_metadata_recursive(meta_root, root_tags)
    for i, ta in enumerate(elem.getElements()):
        if ta.getName() in sub_tags:
            band_view = {}

            if ta.getName() == 'Viewing_Incidence_Angles_Grids':
                band = ta.getAttribute('bandId').getData().getElemString()
                detector = ta.getAttribute('detectorId').getData().getElemString()

            for angle in angle_types:
                if ta.getName() == 'Mean_Sun_Angle':
                    avg_tag = f'Mean_{angle}'
                    sun[avg_tag] = float(ta.getAttribute(f'{angle.upper()}_ANGLE').getData().getElemString())
                else:
                    values_elem = get_metadata_recursive(ta, f'{angle}/Values_List')
                    value_arr = grid_geom(values_elem)

                    if ta.getName() == 'Sun_Angles_Grid':
                        sun[angle] = grid_geom(values_elem)

                    if ta.getName() == 'Viewing_Incidence_Angles_Grids':

                        if band not in view_det:
                            view_det[band] = {}

                        if detector not in view_det[band]:
                            view_det[band][detector] = {}

                        band_view[angle] = copy.copy(value_arr)
                        view_det[band][detector][angle] = copy.copy(value_arr)

            if ta.getName() == 'Viewing_Incidence_Angles_Grids':
                if band not in view:
                    view[band] = band_view
                else:
                    for angle in angle_types:
                        mask = np.isfinite(band_view[angle]) & np.isnan(view[band][angle])
                        view[band][angle][mask] = band_view[angle][mask]

    ave = {}
    for b, band in enumerate(view.keys()):
        for angle in angle_types:
            data = copy.copy(view[band][angle])
            count = np.isfinite(data) * 1
            if b == 0:
                ave[angle] = data
                ave[f'{angle}_Count'] = count
            else:
                ave[angle] += data
                ave[f'{angle}_Count'] += count
    for angle in angle_types:
        view[f'Average_View_{angle}'] = ave[angle] / ave[f'{angle}_Count']

    return sun, view, view_det



