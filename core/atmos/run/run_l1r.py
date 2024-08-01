import numpy as np

from core.atmos.meta import l1r_meta_to_global_attrs, build_angles
from core.atmos.run.l1r import preprocess_l1r_band

def build_l1r(bands:dict, det_band:np.ndarray, det_size:dict, l1r_meta:dict,
              percentiles_compute=True,
              percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    global_attrs, user_settings = l1r_meta_to_global_attrs(l1r_meta)

    #todo: selecting geometric shape of out should be available here
    warp_option_for_angle = (
        global_attrs['scene_proj4_string'],
        [
            min(global_attrs['scene_xrange']), min(global_attrs['scene_yrange']),
            max(global_attrs['scene_xrange']), max(global_attrs['scene_yrange'])
        ],
        global_attrs['scene_pixel_size'][0],
        global_attrs['scene_pixel_size'][1],
        'average' # resampling method
    )

    geometry_type = user_settings['geometry_type']

    det_res = int(det_size['x_res'])

    l1r = build_angles(selected_res=det_res, det_band=det_band,
                       granule_meta=l1r_meta['granule_meta'], geometry_type=geometry_type,
                       warp_option=warp_option_for_angle, index_to_band=global_attrs['index_to_band'],
                       proj_dict=global_attrs['proj_dict'])


    l1r['bands'] = preprocess_l1r_band(bands=bands, user_settings=user_settings, l1r_meta=l1r_meta, global_attrs=global_attrs, warp_option_for_angle=warp_option_for_angle,
                                     percentiles_compute=percentiles_compute, percentiles=percentiles)

    return l1r, global_attrs