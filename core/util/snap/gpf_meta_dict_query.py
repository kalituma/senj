import numpy as np

from core.util import query_dict

def build_sun_angles_meta(meta_dict_query) -> dict:
    # sun
    sun = {}
    sun_angle_grid = meta_dict_query('$.Granules..Sun_Angles_Grid')[0]
    for key, value in sun_angle_grid.items():
        angle_list = []
        if key in ['Zenith', 'Azimuth']:
            for value_line in value['Values_List']['VALUES']:
                angle_list.append([float(value_str) for value_str in value_line.split(' ')])
            sun[key] = np.array(angle_list)

    mean_sun_angle = meta_dict_query('$.Granules..Mean_Sun_Angle')[0]
    sun['Mean_Zenith'] = float(mean_sun_angle['ZENITH_ANGLE'])
    sun['Mean_Azimuth'] = float(mean_sun_angle['AZIMUTH_ANGLE'])

    return sun

def build_grid_meta(meta_dict:dict):

    image_size_list = query_dict('$.Granules..Size', meta_dict)[0]
    grids = {}
    for image_size in image_size_list:
        if image_size['resolution'] not in grids:
            grids[image_size['resolution']] = {}

        for key, value in image_size.items():
            if key in ['NCOLS', 'NROWS']:
                grids[image_size['resolution']][key] = float(value)

    geo_pos_list = query_dict('$.Granules..Geoposition', meta_dict)[0]
    for geo_pos in geo_pos_list:
        if geo_pos['resolution'] not in grids:
            grids[geo_pos['resolution']] = {}

        for key, value in geo_pos.items():
            if key in ['ULX', 'ULY', 'RESOLUTION', 'XDIM', 'YDIM', 'resolution']:
                grids[geo_pos['resolution']][key.upper()] = float(value)

    return grids

def build_view_angles_meta(meta_dict_query):

    view = {}
    view_det = {}

    view_angle_grids = meta_dict_query('$.Granules..Viewing_Incidence_Angles_Grids')[0]
    for view_angle_grid in view_angle_grids:
        band_id = view_angle_grid['bandId']
        detector_id = view_angle_grid['detectorId']

        if band_id not in view_det:
            view[band_id] = {}
            view_det[band_id] = {}

        if detector_id not in view_det[band_id]:
            view_det[band_id][detector_id] = {}

        for angle_key in ['Zenith', 'Azimuth']:
            angle_list = []
            angle_ = view_angle_grid[angle_key]

            for value_line in angle_['Values_List']['VALUES']:
                angle_list.append([float(value_str) for value_str in value_line.split(' ')])
            angle_arr = np.array(angle_list)

            view_det[band_id][detector_id][angle_key] = angle_arr.copy()

            if angle_key not in view[band_id]:
                view[band_id][angle_key] = angle_arr.copy()
            else:
                mask = np.isfinite(angle_arr) & np.isnan(view[band_id][angle_key])
                view[band_id][angle_key][mask] = angle_arr[mask]

    angle_avg = {}

    for band_id, view_row in view.items():
        for angle_key, angle_arr in view_row.items():
            if angle_key not in angle_avg:
                angle_avg[angle_key] = angle_arr.copy()
                angle_avg[f'{angle_key}_cnt'] = np.isfinite(angle_arr) * 1
            else:
                angle_avg[angle_key] += angle_arr.copy()
                angle_avg[f'{angle_key}_cnt'] += np.isfinite(angle_arr) * 1
    angle_avg['Azimuth'] /= angle_avg['Azimuth_cnt']
    angle_avg['Zenith'] /= angle_avg['Zenith_cnt']

    view['Average_View_Zenith'] = angle_avg['Zenith'].copy()
    view['Average_View_Azimuth'] = angle_avg['Azimuth'].copy()

    return view, view_det

def find_grids_and_angle_meta(meta_dict:dict) -> dict:

    # called metadata_granule

    find_meta_dict = lambda x: [field.value for field in parse(x).find(meta_dict)]

    granule_meta = {}

    for key, gen_info in find_meta_dict('$.Granules..General_Info')[0].items():
        if key in ['TILE_ID', 'DATASTRIP_ID', 'SENSING_TIME']:
            granule_meta[key] = gen_info

    granule_meta['HORIZONTAL_CS_NAME'] = find_meta_dict('$.Granules..HORIZONTAL_CS_NAME')[0]
    granule_meta['HORIZONTAL_CS_CODE'] = find_meta_dict('$.Granules..HORIZONTAL_CS_CODE')[0]

    granule_meta['SUN'] = build_sun_angles_meta(find_meta_dict)
    granule_meta['VIEW'], granule_meta['VIEW_DET'] = build_view_angles_meta(find_meta_dict)

    granule_meta['GRANULE_PARENT'] = list(find_meta_dict('$.Granules')[0].keys())[0]

    return granule_meta

def get_granule_info(meta_dict:dict) -> str:
    granule_uri = '$.Level-1C_User_Product..Granule_List.Granule'
    find_meta_dict = lambda x: [field.value for field in parse(x).find(meta_dict)]
    granule_dict = find_meta_dict(granule_uri)[0]
    if len(granule_dict['IMAGE_FILE']) > 1:
        granule_info = granule_dict['IMAGE_FILE'][0].split('/')[1]
    else:
        granule_info = ''

    return granule_info


