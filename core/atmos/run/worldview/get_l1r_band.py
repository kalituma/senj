import numpy as np
from core.util import Logger

def get_l1r_band(bands, band_info, gains, gains_parameter, se_distance, mus, f0_b, waves_names, waves_mu,
                 percentiles_compute, percentiles,
                 atmospherically_corrected):

    dtype_zero_map = {
            np.dtype('uint8'): np.uint8(0),
            np.dtype('uint16'): np.uint16(0),
            np.dtype('int8'): np.int8(0),
            np.dtype('int16'): np.int16(0),
            np.dtype('int32'): np.int32(0),
            np.dtype('uint32'): np.uint32(0),
            np.dtype('float32'): np.float32(0),
            np.dtype('float64'): np.float64(0)
        }
    
    out = {}
    ## run through bands
    for band_name, band in bands.items():
        band_slot = band['slot']
        d = band['value'].copy()
        cf = float(band_info[band_name]['ABSCALFACTOR']) / float(band_info[band_name]['EFFECTIVEBANDWIDTH'])

        if cf <= 0:
            Logger.get_logger().log('info', 'Warning DN scaling factor is <0, this will give bad TOA radiances/reflectances.')
            # if 'RADIOMETRICENHANCEMENT' in meta:
        #         print('Data has been enhanced by the provider: {}'.format(meta['RADIOMETRICENHANCEMENT']))

        ## track mask
        if d.dtype in dtype_zero_map:
            nodata = d == dtype_zero_map[d.dtype]
        else:
            nodata = d == 0

        ## convert to float and scale to TOA reflectance
        d = d.astype(np.float32) * cf
        if gains != None and gains_parameter == 'radiance':
            Logger.get_logger().log('info', 'Applying gain {} and offset {} to TOA radiance for band {}'.format(gains[band]['gain'],gains[band]['offset'],band))
            d = gains[band_slot]['gain'] * d + gains[band_slot]['offset']

        d *= (np.pi * se_distance ** 2) / (f0_b[band_slot] / 10. * mus)

        if gains != None and gains_parameter == 'reflectance':
            Logger.get_logger().log('info', 'Applying gain {} and offset {} to TOA reflectance for band {}'.format(gains[band]['gain'],gains[band]['offset'], band))
            d = gains[band_slot]['gain'] * d + gains[band_slot]['offset']

        ## apply mask
        d[nodata] = np.nan

        ## set up dataset attributes
        ds = f'rhot_{waves_names[band_slot]}'
        if atmospherically_corrected:
            ds = ds.replace('rhot_', 'rhos_acomp_')

        l1r_band_attr = {'wavelength': waves_mu[band_slot] * 1000, 'band_name': band_name, 'f0': f0_b[band_slot] / 10.,
                         'parameter' : ds }
        if gains != None:
            l1r_band_attr['gain'] = gains[band_slot]['gain']
            l1r_band_attr['offset'] = gains[band_slot]['offset']
            l1r_band_attr['gains_parameter'] = gains_parameter
        if percentiles_compute:
            l1r_band_attr['percentiles'] = percentiles
            l1r_band_attr['percentiles_data'] = np.nanpercentile(d, percentiles)

        out[band_slot] = {
            'data': d,
            'att': l1r_band_attr
        }

    return out