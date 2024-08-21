import numpy as np

def get_l1r_band(bands, band_info, gains, gains_parameter, se_distance, mus, f0_b, waves_names, waves_mu,
                 percentiles_compute, percentiles,
                 atmospherically_corrected):

    out = {}
    ## run through bands
    for band_name, band in bands.items():
        band_slot = band['slot']
        d = band['value'].copy()
        cf = float(band_info[band_name]['ABSCALFACTOR']) / float(band_info[band_name]['EFFECTIVEBANDWIDTH'])

        # if cf <= 0:
        #     print('Warning DN scaling factor is <0, this will give bad TOA radiances/reflectances.')
        #     if 'RADIOMETRICENHANCEMENT' in meta:
        #         print('Data has been enhanced by the provider: {}'.format(meta['RADIOMETRICENHANCEMENT']))

        ## track mask
        if d.dtype == np.dtype('uint8'):
            nodata = d == np.uint8(0)
        elif d.dtype == np.dtype('uint16'):
            nodata = d == np.uint16(0)
        elif d.dtype == np.dtype('float32'):
            nodata = d == np.float32(0)

        ## convert to float and scale to TOA reflectance
        d = d.astype(np.float32) * cf
        if gains != None and gains_parameter == 'radiance':
            # print('Applying gain {} and offset {} to TOA radiance for band {}'.format(gains[band]['gain'],gains[band]['offset'],band))
            d = gains[band_slot]['gain'] * d + gains[band_slot]['offset']

        d *= (np.pi * se_distance ** 2) / (f0_b[band_slot] / 10. * mus)

        if gains != None and gains_parameter == 'reflectance':
            # print('Applying gain {} and offset {} to TOA reflectance for band {}'.format(gains[band]['gain'],gains[band]['offset'], band))
            d = gains[band_slot]['gain'] * d + gains[band_slot]['offset']

        ## apply mask
        d[nodata] = np.nan

        ## set up dataset attributes
        ds = f'rhot_{waves_names[band_slot]}'
        if atmospherically_corrected:
            ds = ds.replace('rhot_', 'rhos_acomp_')

        l1r_band_attr = {'wavelength': waves_mu[band_slot] * 1000, 'band_slot': band_slot, 'f0': f0_b[band_slot] / 10.,
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