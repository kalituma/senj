from typing import Union, TYPE_CHECKING

from core.util import glob_match
from core.atmos.run import load_bands
from core.atmos.run.sentinel import get_l1r_band, build_det_grid, meta_dict_to_l1r_meta, load_det, l1r_meta_to_global_attrs, init_l1r

if TYPE_CHECKING:
    from core.raster import Raster

def get_geo_info_from_meta(meta, geom_res, prefix=""):

    src_params = {}
    src_params['ydim'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['NROWS']
    src_params['xdim'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['NCOLS']
    src_params['ul_x'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['ULX']
    src_params['ul_y'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['ULY']
    src_params['epsg'] = int(meta['HORIZONTAL_CS_CODE'].split(':')[1])
    src_params['pixel_size'] = meta[f'{prefix}GRIDS'][f'{geom_res}']['RESOLUTION']

    return src_params

def build_sentinel_l1r(target_raster: "Raster", target_band_names:list[str], target_band_slot:list[str], det_bands:Union[str, list[str]],
                       user_settings:dict, percentiles_compute=True, percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):


    l1r_meta = meta_dict_to_l1r_meta(target_raster)

    res_set = set()
    for bname in target_band_names:
        x_res = int(l1r_meta['size_meta_per_band'][bname]['x_res'])
        if x_res not in res_set:
            res_set.add(x_res)

    all_bands = target_raster.get_band_names()
    if isinstance(det_bands, str):
        # find the band with glob pattern with asterisk described in det_bands
        det_bands = glob_match(all_bands, det_bands)
    elif isinstance(det_bands, list):
        det_bands = det_bands
    else:
        raise ValueError('det_bands should be either a string or a list of strings.')

    assert len(det_bands) > 0, 'No matching band found in target raster.'

    # read det
    det_dict, det_names = load_det(target_raster, det_bands=det_bands, size_per_band=l1r_meta['size_meta_per_band'],
                                   det_res=list(res_set))

    target_raster = load_bands(target_raster, target_band_names, target_band_slot)

    # det_sizes = { det_name : l1r_meta['size_meta_per_band'][det_name] for det_name in det_names}
    l1r_meta['granule_meta']['GRIDS'] = build_det_grid(target_raster, det_names)

    # todo: load band to cache if it is not already loaded
    global_attrs, user_settings = l1r_meta_to_global_attrs(l1r_meta, user_settings)

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

    in_width, in_height = l1r_meta['granule_meta']['GRIDS'][f'{det_res}']['NCOLS'], l1r_meta['granule_meta']['GRIDS'][f'{det_res}']['NROWS']
    geo_info = get_geo_info_from_meta(l1r_meta['granule_meta'], det_res)
    l1r = init_l1r(width=in_width, height=in_height, geo_info=geo_info, det_band=det_band,
                   granule_meta=l1r_meta['granule_meta'], geometry_type=geometry_type,
                   warp_option=warp_option_for_angle, index_to_band=global_attrs['index_to_band'],
                   proj_dict=global_attrs['proj_dict'])

    l1r['bands'] = get_l1r_band(bands=target_raster.bands, user_settings=user_settings, l1r_meta=l1r_meta,
                                global_attrs=global_attrs, warp_option_for_angle=warp_option_for_angle,
                                percentiles_compute=percentiles_compute, percentiles=percentiles,
                                geo_info_func=get_geo_info_from_meta)

    return l1r, global_attrs