import numpy as np
import scipy.ndimage

from core.raster.gpf_module import get_src_param, warp_to

def preprocess_l1r_band(bands:dict, user_settings:dict, l1r_meta:dict, global_attrs:dict, warp_option_for_angle:tuple,
                        percentiles_compute:bool, percentiles:tuple):

    nodata = int(l1r_meta['product_info']['NODATA'])
    quant = float(l1r_meta['product_info']['QUANTIFICATION_VALUE'])

    granule_meta = l1r_meta['granule_meta']
    band_info = l1r_meta['sensor_response']

    dilate = user_settings['s2_dilate_blackfill']
    dilate_iterations = user_settings['s2_dilate_blackfill_iterations']

    gains = user_settings['gains']
    offsets = user_settings['offsets']

    wave_names = global_attrs['wave_names']
    wave_mu = global_attrs['wave_mu']
    gains_dict = global_attrs['gains_dict']
    offsets_dict = global_attrs['offsets_dict']

    out = {}
    for band_name, band in bands.items():
        b_slot_id = band_name[1:]
        band_value = band['value']
        b_res = int(band_info['Resolution'][band_name])

        if b_slot_id in wave_names:
            l1r_band_attr = {}
            src_params = get_src_param(granule_meta, b_res)
            band_value = warp_to(src_params, band_value, warp_to=warp_option_for_angle).astype(np.float32)

            band_mask = band_value == nodata
            if dilate:
                band_mask = scipy.ndimage.binary_dilation(band_mask, iterations=dilate_iterations)

            if 'RADIO_ADD_OFFSET' in band_info:
                band_value += band_info['RADIO_ADD_OFFSET'][band_name]

            band_value /= quant
            band_value[band_mask] = np.nan

            l1r_band_attr['wavelength'] = wave_mu[b_slot_id] * 1000
            l1r_band_attr['rhot_ds'] = f'rhot_{wave_names[b_slot_id]}'

            if gains & (gains_dict is not None):
                l1r_band_attr['toa_gain'] = gains_dict[b_slot_id]
                band_value *= gains_dict[b_slot_id]

            if offsets & (offsets_dict is not None):
                l1r_band_attr['toa_offset'] = offsets_dict[b_slot_id]
                band_value += offsets_dict[b_slot_id]

            if percentiles_compute:
                l1r_band_attr['percentiles'] = percentiles
                l1r_band_attr['percentiles_data'] = np.nanpercentile(band_value, percentiles)

            out[band_name] = {
                'data' : band_value,
                'att' : l1r_band_attr
            }
        else:
            continue
    return out