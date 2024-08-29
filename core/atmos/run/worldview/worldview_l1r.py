from typing import TYPE_CHECKING


import core.atmos as atmos
from core.atmos.run import load_proj_from_raw
from core.atmos.run.worldview import init_l1r, get_l1r_band, meta_dict_to_global_attrs

if TYPE_CHECKING:
    from core.raster import Raster

def build_worldview_l1r(target_raster: "Raster", target_band_names:list[str], meta_dict:dict, user_settings:dict,
                        percentiles_compute=True, percentiles=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    target_band_slot = [target_raster[bname]['slot'].lower() for bname in target_band_names]
    for slot in target_band_slot:
        assert slot in ['blue', 'green', 'red', 'nir', 'nir1', 'nir2', 'pan'], f'Invalid band slot: {slot}'

    ## test if we need to do an atmospheric correction
    atmospherically_corrected = False
    if 'RADIOMETRICLEVEL' in meta_dict and 'RADIOMETRICENHANCEMENT' in meta_dict:
        if meta_dict['RADIOMETRICENHANCEMENT'] in ['ACOMP']:
            # print('Image {} is already corrected by supplier.'.format(bundle))
            # print('RADIOMETRICLEVEL: {} RADIOMETRICENHANCEMENT: {}'.format(meta['RADIOMETRICLEVEL'],meta['RADIOMETRICENHANCEMENT']))
            atmospherically_corrected = True

    output_geolocation = user_settings['output_geolocation']
    global_attrs = meta_dict_to_global_attrs(meta_dict, user_settings, atmospherically_corrected=atmospherically_corrected)

    ## global scene dimensions from metadata
    global_dims = [int(meta_dict['NUMROWS']), int(meta_dict['NUMCOLUMNS'])]
    proj_dict = load_proj_from_raw(target_raster.raw, target_raster.module_type)

    ## add projection to gatts
    for k in ['xrange', 'yrange', 'proj4_string', 'pixel_size', 'dimensions', 'zone']:
        if k in proj_dict:
            global_attrs[k] = proj_dict[k]

    nc_projection = atmos.shared.projection_netcdf(proj_dict, add_half_pixel=False)
    global_attrs['projection_key'] = [k for k in nc_projection if k not in ['x', 'y']][0]

    # target_raster = load_bands(target_raster, target_band_names, target_band_slot)

    l1r = init_l1r(proj_dict, global_dims=global_dims, meta_dict=meta_dict, output_geolocation=output_geolocation)

    l1r['bands'] = get_l1r_band(bands=target_raster.bands, band_info=meta_dict['BAND_INFO'],
                                gains=global_attrs['gains'], gains_parameter=user_settings['gains_parameter'],
                                se_distance=global_attrs['se_distance'], mus=global_attrs['mus'],
                                f0_b=global_attrs['f0_b'], waves_names=global_attrs['waves_names'], waves_mu=global_attrs['waves_mu'],
                                percentiles_compute=percentiles_compute, percentiles=percentiles,
                                atmospherically_corrected=atmospherically_corrected)
    return l1r, global_attrs
