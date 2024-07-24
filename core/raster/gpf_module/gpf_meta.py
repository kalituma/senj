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
    return build_meta_dict(product.getMetadataRoot())

def set_meta_to_product(product:Product, meta_dict:dict):

    metadata_element = jpy.get_type('org.esa.snap.core.datamodel.MetadataElement')

    meta_root = product.getMetadataRoot()
    for key, _ in meta_dict.items():
        if not meta_root.containsElement(key):
            sub_elem = set_meta_recursive(metadata_element(key), meta_dict[key])
            meta_root.addElement(sub_elem)

    return product

def read_granule_meta(product:Product) -> dict:

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
    granule_meta['OR_GRIDS'] = grids

    sun, view, view_det = _parse_tile_angle(meta_root, granule_par_tag)
    granule_meta['SUN'] = sun
    granule_meta['VIEW'] = view
    granule_meta['VIEW_DET'] = view_det
    granule_meta['GRANULE_PARENT'] = granule_par_tag

    return granule_meta

def make_gattr(product:Product):

    input_file = str(product.getFileLocation())

    product_meta_root = product.getMetadataRoot()
    gr_meta = read_granule_meta(product_meta_root)

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

def build_angles(det_bands, gr_meta, geom_res, geometry_type, warp_option, rsr_bands, cur_dct):

    out = {}

    or_x_height = gr_meta['OR_GRIDS'][f'{geom_res}']['NCOLS']
    or_y_height = gr_meta['OR_GRIDS'][f'{geom_res}']['NROWS']

    xnew = np.linspace(0, gr_meta['VIEW']['Average_View_Zenith'].shape[1] - 1, int(or_x_height))
    ynew = np.linspace(0, gr_meta['VIEW']['Average_View_Zenith'].shape[0] - 1, int(or_y_height))
    sza = tiles_interp(gr_meta['SUN']['Zenith'], xnew, ynew, smooth=False, method='linear')
    saa = tiles_interp(gr_meta['SUN']['Azimuth'], xnew, ynew, smooth=False, method='linear')

    if geometry_type == 'grids':
        vza = tiles_interp(gr_meta['VIEW']['Average_View_Zenith'], xnew, ynew, smooth=False, method='nearest')
        vaa = tiles_interp(gr_meta['VIEW']['Average_View_Azimuth'], xnew, ynew, smooth=False, method='nearest')

    ## use s2 5x5 km grids with detector footprint interpolation
    dfoo = None
    bands = None
    if geometry_type == 'grids_footprint':
        # for band in product.getBands():
        band_name = res_band_map[f'{geom_res}']
        dfoo = det_bands[f'{band_name}']
        dval = np.unique(dfoo)

        bands = [str(bi) for bi, b in enumerate(rsr_bands)]

        vza = np.zeros((int(or_y_height), int(or_x_height))) + np.nan
        vaa = np.zeros((int(or_y_height), int(or_x_height))) + np.nan

        for nf, bv in enumerate(dval):
            if bv == 0:
                continue

            ave_vza = None
            ave_vaa = None
            for b in bands:
                if b not in gr_meta['VIEW_DET']: continue
                if f'{bv}' not in gr_meta['VIEW_DET'][b]: continue
                bza = gr_meta['VIEW_DET'][b][f'{bv}']['Zenith']
                baa = gr_meta['VIEW_DET'][b][f'{bv}']['Azimuth']
                bza = grid_extend(bza, iterations=1, crop=False)
                baa = grid_extend(baa, iterations=1, crop=False)
                if ave_vaa is None:
                    ave_vza = bza
                    ave_vaa = baa
                else:
                    ave_vza = np.dstack((ave_vza, bza))
                    ave_vaa = np.dstack((ave_vaa, baa))
        # if verbosity > 1: print('Computing band average per detector geometry')

            if ave_vza is not None:
                ave_vza = np.nanmean(ave_vza, axis=2)
                ave_vaa = np.nanmean(ave_vaa, axis=2)
                ## end compute detector average geometry
                ## interpolate grids to current detector
                det_mask = dfoo == bv

                ## add +1 to xnew and ynew since we are not cropping the extended grid
                vza[det_mask] = tiles_interp(ave_vza, xnew + 1, ynew + 1, smooth=False, fill_nan=True,
                                             target_mask=det_mask, target_mask_full=False, method='linear')

                vaa[det_mask] = tiles_interp(ave_vaa, xnew + 1, ynew + 1, smooth=False, fill_nan=True,
                                             target_mask=det_mask, target_mask_full=False, method='linear')

    src_params = get_src_param(gr_meta, geom_res, prefix="OR_")

    # resample to new geometry
    sza = warp_to(src_params, sza, warp_to=warp_option)
    saa = warp_to(src_params, saa, warp_to=warp_option)
    vza = warp_to(src_params, vza, warp_to=warp_option)
    vaa = warp_to(src_params, vaa, warp_to=warp_option)
    mask = (vaa == 0) * (vza == 0) * (saa == 0) * (sza == 0)

    out['dfoo'] = dfoo
    vza[mask] = np.nan
    sza[mask] = np.nan
    vaa[mask] = np.nan
    saa[mask] = np.nan
    out['vaa'] = vaa
    out['saa'] = saa
    out['vza'] = vza
    out['sza'] = sza

    raa = np.abs(saa - vaa)
    tmp = np.where(raa > 180)
    raa[tmp] = np.abs(360 - raa[tmp])
    raa[mask] = np.nan
    out['raa'] = raa

    lon, lat = projection_geo(cur_dct, add_half_pixel=True)
    out['lon'] = lon.astype(np.float32)
    out['lat'] = lat.astype(np.float32)

    return out

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

def metadata_scene(product:Product, metadata:dict) -> tuple[dict, dict]:

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

    meta = {}

    for i, uri in enumerate(product_info_uri):
        for attr_tag in product_info_tags[i]:
            child_uri = f'{uri}/{attr_tag}'
            value = get_metadata_value(meta_root, child_uri)
            meta[attr_tag] = value

    special_uri = product_info_uri[3]
    special_tag = 'Special_Values'

    special_par = get_metadata_recursive(meta_root, f'{special_uri}')
    for special in special_par.getElements():
        if special.getName() != special_tag:
            continue
        fill = special.getAttribute('SPECIAL_VALUE_TEXT').getData().getElemString()
        fill_value = special.getAttribute('SPECIAL_VALUE_INDEX').getData().getElemString()
        meta[fill] = fill_value


    product_info_uri = [
        '$.Level-1C_User_Product.General_Info.Product_Info',
        '$.Level-1C_User_Product.General_Info.Product_Info.Datatake',
        '$.Level-1C_User_Product.General_Info.Product_Info.Query_Options',
        '$.Level-1C_User_Product.General_Info.Product_Image_Characteristics',
        '$.Level-1C_User_Product.General_Info.Product_Image_Characteristics.Reflectance_Conversion'
    ]

    reflectance_metadata = {}
    find_product = lambda x: [field.value for field in parse(x).find(metadata)]

    for i, uri in enumerate(product_info_uri):
        info_node = find_product(uri)[0]
        for attr_tag in product_info_tags[i]:
            value = info_node[attr_tag]
            reflectance_metadata[attr_tag] = value

    # special values
    special_uri = product_info_uri[3]
    special_tag = 'Special_Values'

    special_par = get_metadata_recursive(meta_root, f'{special_uri}')
    for special in special_par.getElements():
        if special.getName() != special_tag:
            continue
        fill = special.getAttribute('SPECIAL_VALUE_TEXT').getData().getElemString()
        fill_value = special.getAttribute('SPECIAL_VALUE_INDEX').getData().getElemString()
        meta[fill] = fill_value

    banddata = {}
    banddata['BandNames'] = {}
    banddata['Resolution'] = {}
    banddata['Wavelength'] = {}
    banddata['RSR'] = {}

    spectral_uri = f'{product_info_uri[3]}/Spectral_Information_List'
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
        banddata['Wavelength'][band] = {tag:float(get_metadata_value(spectral, f'Wavelength/{tag}')) for tag in ['CENTRAL', 'MIN', 'MAX']}

        step = get_metadata_value(spectral, 'Spectral_Response/STEP')
        values = get_metadata_value(spectral, 'Spectral_Response/VALUES')
        rsr = [float(rs) for rs in values.split(' ')]

        wave = np.linspace(
            float(banddata['Wavelength'][band]['MIN']), \
            float(banddata['Wavelength'][band]['MAX']), \
            int((float(banddata['Wavelength'][band]['MAX']) - float(banddata['Wavelength'][band]['MIN'])) / float(step) + 1)
        )

        banddata['RSR'][band] = {'response': rsr, 'wave': wave}

    if len(banddata['BandNames']) == 0:
        banddata['BandNames'] = {'0': 'B1', '1': 'B2', '2': 'B3', '3': 'B4', '4': 'B5', '5': 'B6', '6': 'B7',
                                 '7': 'B8', '8': 'B8A', '9': 'B9', '10': 'B10', '11': 'B11', '12': 'B12'}


    f_uri = f'{product_info_uri[4]}/Solar_Irradiance_List'
    if 'F0' not in banddata: banddata['F0'] = {}
    for bi, f in enumerate(get_metadata_recursive(meta_root, f_uri).getAttributes()):
        band = f'B{bi}'
        banddata['F0'][band] = float(f.getData().getElemString())

    phy_uri = f'{product_info_uri[3]}'
    phy_tag = 'PHYSICAL_GAINS'
    for bi, t in enumerate(get_metadata_recursive(meta_root, phy_uri).getAttributes()):
        if phy_tag not in banddata: banddata[phy_tag] = {}
        if t.getName() != phy_tag:
            continue

        band = f'B{bi}'
        banddata[phy_tag][band] = float(t.getData().getElemString())

    rad_uri = f'{product_info_uri[3]}/Radiometric_Offset_List'
    rad_tag = 'RADIO_ADD_OFFSET'
    for bi, t in enumerate(get_metadata_recursive(meta_root, rad_uri).getAttributes()):
        if rad_tag not in banddata: banddata[rad_tag] = {}
        if t.getName() != rad_tag:
            continue
        band = banddata['BandNames'][f'{bi}']
        banddata[rad_tag][band] = float(t.getData().getElemString())

    return meta, banddata

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
            grids[res][tag] = int(value)

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



def get_res_per_band(product:Product) -> dict:
    pass

