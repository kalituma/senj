from typing import TYPE_CHECKING

from core.atmos.run.planet import init_l1r, get_l1r_band, meta_dict_to_global_attrs
from core.atmos.run import load_bands, load_proj_from_raw
from core.atmos.shared import read_tif_meta

if TYPE_CHECKING:
    from core.raster import Raster

def build_planet_l1r(target_raster: "Raster", target_band_names:list[str], target_band_slot:list[str], meta_dict:dict, user_settings:dict,
                     percentiles_compute=True, percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    assert len(target_band_names) == len(target_band_slot), 'target_band_names and target_band_slot must have the same length'
    target_band_slot = [slot.lower() for slot in target_band_slot]
    for slot in target_band_slot:
        assert slot in ['blue', 'green', 'red', 'nir'], f'Invalid band slot: {slot}'

    output_geolocation = user_settings['output_geolocation']
    output_xy = user_settings['output_xy']
    # netcdf_projection = user_settings['netcdf_projection']

    global_attrs = meta_dict_to_global_attrs(meta_dict, user_settings)
    proj_dict = load_proj_from_raw(target_raster.raw, target_raster.module_type)

    global_attrs['scene_xrange'] = proj_dict['xrange']
    global_attrs['scene_yrange'] = proj_dict['yrange']
    global_attrs['scene_proj4_string'] = proj_dict['proj4_string']
    global_attrs['scene_pixel_size'] = proj_dict['pixel_size']
    global_attrs['scene_dims'] = proj_dict['dimensions']
    if 'zone' in proj_dict:
        global_attrs['scene_zone'] = proj_dict['zone']

    dct_prj = {k: proj_dict[k] for k in proj_dict}

    pkeys = ['xrange', 'yrange', 'proj4_string', 'pixel_size', 'zone']
    for k in pkeys:
        if k in dct_prj:
            global_attrs[k] = dct_prj[k]

    ## store scene and output dimensions
    global_attrs['scene_dims'] = proj_dict['ydim'], proj_dict['xdim']
    global_attrs['global_dims'] = dct_prj['dimensions']

    l1r = init_l1r(dct_prj, output_geolocation=output_geolocation, output_xy=output_xy)
    band_indices = {f'{slot}-band_idx': i for i, slot in enumerate(target_band_slot)}
    tif_meta = read_tif_meta(target_raster.path)
    f0_dict = {f'{slot}_f0': global_attrs[f'{slot}_f0'] for slot in target_band_slot}
    value_conversion = {}

    for slot in target_band_slot:
        s_case_list = [slot.title(), slot.lower(), slot.upper()]
        for s_case in s_case_list:
            ref_conv_key = f'{s_case}-to_reflectance'
            rad_conv_key = f'{s_case}-to_radiance'

            if ref_conv_key in meta_dict:
                value_conversion[ref_conv_key.lower()] = meta_dict[ref_conv_key]

            if rad_conv_key in meta_dict:
                value_conversion[rad_conv_key.lower()] = meta_dict[rad_conv_key]

    assert len(value_conversion) == 2 * len(target_band_slot), 'value_conversion must have 2 entries per band slot'

    target_raster = load_bands(target_raster, target_band_names, target_band_slot)

    l1r['bands'] = get_l1r_band(target_raster.bands, band_indices=band_indices, tif_meta=tif_meta, f0_dict=f0_dict, sensor=meta_dict['sensor'],
                                se_distance=global_attrs['se_distance'], mus=global_attrs['mus'], waves_names=global_attrs['wave_names'], waves_mu=global_attrs['wave_mu'],
                                value_conversion=value_conversion, gains=user_settings['gains'], gains_dict=global_attrs['gains_dict'],
                                percentiles_compute=percentiles_compute, percentiles=percentiles)

    return l1r, global_attrs

