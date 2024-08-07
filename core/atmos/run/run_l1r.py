import numpy as np

from core.atmos.meta import l1r_meta_to_global_attrs, build_angles
from core.atmos.run.l1r import preprocess_l1r_band

def build_l1r(bands:dict, det_dict:dict, det_sizes:dict, l1r_meta:dict,
              percentiles_compute=True,
              percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    global_attrs, user_settings = l1r_meta_to_global_attrs(l1r_meta)

    warp_option_for_angle = (
        global_attrs['scene_proj4_string'],
        [
            min(global_attrs['proj_dict']['xrange']), min(global_attrs['proj_dict']['yrange']),
            max(global_attrs['proj_dict']['xrange']), max(global_attrs['proj_dict']['yrange'])
        ],
        global_attrs['proj_dict']['pixel_size'][0],
        global_attrs['proj_dict']['pixel_size'][1],
        'average'  # resampling method
    )

    # geometry_res = user_settings['geometry_res']
    geometry_type = user_settings['geometry_type']

    det_res = user_settings['geometry_res']
    det_band = det_dict[f'{det_res}']

    l1r = build_angles(det_res=det_res, det_band=det_band,
                       granule_meta=l1r_meta['granule_meta'], geometry_type=geometry_type,
                       warp_option=warp_option_for_angle, index_to_band=global_attrs['index_to_band'],
                       proj_dict=global_attrs['proj_dict'])


    l1r['bands'] = preprocess_l1r_band(bands=bands, user_settings=user_settings, l1r_meta=l1r_meta, global_attrs=global_attrs, warp_option_for_angle=warp_option_for_angle,
                                     percentiles_compute=percentiles_compute, percentiles=percentiles)

    return l1r, global_attrs