import os
import numpy as np
import scipy.ndimage

from core import atmos, PROJECT_PATH
from core.raster.gpf_module import projection_from_meta, get_src_param, warp_to, build_angles, copy_dct_to_atts
from core.util import rsr_convolute_dict, rsr_read


def _l1r_postprocess(out, bands, rsr_bands, wave, percentiles_compute, percentiles, warp_option_for_angle, setu, gatts):

    gains = setu['gains']
    gains_toa = setu['gains_toa']
    offsets = setu['offsets']
    offsets_toa = setu['offsets_toa']
    band_data = gatts['band_data']

    # gains
    gains_dict = None
    if gains & (gains_toa is not None):
        if len(gains_toa) == len(rsr_bands):
            gains_dict = {b: float(gains_toa[ib]) for ib, b in enumerate(rsr_bands)}

    ## offsets
    offsets_dict = None
    if offsets & (offsets_toa is not None):
        if len(offsets_toa) == len(rsr_bands):
            offsets_dict = {b: float(offsets_toa[ib]) for ib, b in enumerate(rsr_bands)}

    dilate = setu['s2_dilate_blackfill']
    dilate_iterations = setu['s2_dilate_blackfill_iterations']

    gr_meta = gatts['gr_meta']
    nodata = gatts['nodata']

    quant = gatts['quant']

    out['bands'] = {}
    for bi, b in enumerate(rsr_bands):
        Bn = f'B{b}'
        b_res = int(band_data['Resolution'][Bn])

        if b in wave['wave_names']:
            src_params = get_src_param(gr_meta, b_res, prefix="CUR_")
            data = warp_to(src_params, bands[Bn], warp_to=warp_option_for_angle, type='uint')
            data_mask = data == nodata
            if dilate:
                data_mask = scipy.ndimage.binary_dilation(data_mask, iterations=dilate_iterations)

            data = data.astype(np.float32)
            if 'RADIO_ADD_OFFSET' in band_data:
                data += band_data['RADIO_ADD_OFFSET'][Bn]
            data /= quant
            data[data_mask] = np.nan
            ds_att = {'wavelength': wave['wave_mu'][b] * 1000}
            ds_att['rhot_ds'] = f'rhot_{wave["wave_names"][b]}'

            if gains & (gains_dict is not None):
                ds_att['toa_gain'] = gains_dict[b]
                data *= ds_att['toa_gain']
                print(f'Converting bands: Applied TOA gain {ds_att["toa_gain"]} to {Bn}')

            if offsets & (offsets_dict is not None):
                ds_att['toa_offset'] = offsets_dict[b]
                data *= ds_att['toa_offset']
                print(f'Converting bands: Applied TOA offset {ds_att["toa_gain"]} to {Bn}')

            # for k in band_data: ds_att[k] = band_data[k][b]
            if percentiles_compute:
                ds_att['percentiles'] = percentiles
                ds_att['percentiles_data'] = np.nanpercentile(data, percentiles)

            out['bands'][Bn] = {
                'data': data,
                'att': ds_att
            }
        else:
            continue

    return out

def prepare_l1r(bands, det_bands, gatts, input_path, output_path, percentiles_compute:bool=True, percentiles:set=(0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100)):

    setu = {k: atmos.settings['run'][k] for k in atmos.settings['run']}

    gatts['inputfile'] = input_path
    gatts['output'] = output_path

    sensor = gatts['sensor']
    setu = atmos.setting.parse(sensor, settings=setu)

    s2_target_res = setu['s2_target_res']
    geometry_type = setu['geometry_type']
    geometry_res = setu['geometry_res']
    gr_meta = gatts['gr_meta']
    or_dct, cur_dct = projection_from_meta(gr_meta, s2_target_res=int(s2_target_res))

    or_global_dims = or_dct['dimensions']
    cur_global_dims = cur_dct['dimensions']

    rsrf = os.path.join(PROJECT_PATH, 'data', 'atmos', 'RSR', f'{sensor}.txt')
    rsr, rsr_bands = rsr_read(rsrf)

    waves = np.arange(250, 2500) / 1000
    waves_mu = rsr_convolute_dict(waves, waves, rsr)
    waves_names = {f'{b}': f'{waves_mu[b] * 1000:.0f}' for b in waves_mu}

    wave = {
        'waves': waves,
        'wave_mu': waves_mu,
        'wave_names': waves_names
    }

    # get F0 - not stricty necessary if using USGS reflectance
    f0 = atmos.shared.f0_get(f0_dataset=setu['solar_irradiance_reference'])
    f0_b = rsr_convolute_dict(np.asarray(f0['wave']) / 1000, np.asarray(f0['data']) * 10, rsr)

    gatts['or_global_dims'] = or_global_dims
    gatts['cur_global_dims'] = cur_global_dims

    for b in rsr_bands:
        gatts[f'{b}_wave'] = waves_mu[b] * 1000
        gatts[f'{b}_name'] = waves_names[b]
        gatts[f'{b}_f0'] = f0_b[b]

    gatts = copy_dct_to_atts(or_dct, gatts, prefix='or_')
    gatts = copy_dct_to_atts(cur_dct, gatts, prefix='cur_')

    xyr = [
        min(gatts['cur_scene_xrange']),
        min(gatts['cur_scene_yrange']),
        max(gatts['cur_scene_xrange']),
        max(gatts['cur_scene_yrange'])
    ]

    proj_str = gatts['cur_scene_proj4_string']
    scene_boundary = xyr
    pixel_size_x = gatts['cur_scene_pixel_size'][0]
    pixel_size_y = gatts['cur_scene_pixel_size'][1]
    res_method = 'average'

    warp_option_for_angle = (proj_str, scene_boundary, pixel_size_x, pixel_size_y, res_method)
    out = build_angles(det_bands, gatts['gr_meta'], geometry_res, geometry_type, warp_option_for_angle, rsr_bands, cur_dct)
    out = _l1r_postprocess(out, bands, rsr_bands, wave, percentiles_compute, percentiles, warp_option_for_angle, setu, gatts)

    return out, gatts