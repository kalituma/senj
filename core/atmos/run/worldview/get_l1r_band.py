
def get_l1r_band(bands):
    ## run through bands
    for b, band in enumerate(band_names):

        ## get tile offset
        offset = [int(tile_info['ULCOLOFFSET']), int(tile_info['ULROWOFFSET'])]


        if 'SWIR' not in band:
            bt = [bt for bt in meta_dict['BAND_INFO'] if meta_dict['BAND_INFO'][bt]['name'] == band][0]
            d = ac.shared.read_band(file, idx=meta['BAND_INFO'][bt]['index'], sub=sub, warp_to=warp_to)
            cf = float(meta['BAND_INFO'][bt]['ABSCALFACTOR']) / float(
                meta['BAND_INFO'][bt]['EFFECTIVEBANDWIDTH'])
        else:
            if swir_file is None:
                swir_file = '{}'.format(file)
                swir_meta = meta.copy()
            bt = [bt for bt in swir_meta['BAND_INFO'] if swir_meta['BAND_INFO'][bt]['name'] == band][0]
            d = ac.shared.read_band(swir_file, idx=swir_meta['BAND_INFO'][bt]['index'], sub=sub,
                                    warp_to=warp_to)
            cf = float(swir_meta['BAND_INFO'][bt]['ABSCALFACTOR']) / float(
                swir_meta['BAND_INFO'][bt]['EFFECTIVEBANDWIDTH'])

            if cf <= 0:
                print('Warning DN scaling factor is <0, this will give bad TOA radiances/reflectances.')
                if 'RADIOMETRICENHANCEMENT' in meta:
                    print('Data has been enhanced by the provider: {}'.format(meta['RADIOMETRICENHANCEMENT']))

            ## track mask
            if d.dtype == np.dtype('uint8'):
                nodata = d == np.uint8(0)
            elif d.dtype == np.dtype('uint16'):
                nodata = d == np.uint16(0)

            ## convert to float and scale to TOA reflectance
            d = d.astype(np.float32) * cf
            if (gains != None) & (setu['gains_parameter'] == 'radiance'):
                print('Applying gain {} and offset {} to TOA radiance for band {}'.format(gains[band]['gain'],
                                                                                          gains[band]['offset'],
                                                                                          band))
                d = gains[band]['gain'] * d + gains[band]['offset']
            d *= (np.pi * gatts['se_distance'] ** 2) / (f0_b[band] / 10. * gatts['mus'])
            if (gains != None) & (setu['gains_parameter'] == 'reflectance'):
                print(
                    'Applying gain {} and offset {} to TOA reflectance for band {}'.format(gains[band]['gain'],
                                                                                           gains[band][
                                                                                               'offset'], band))
                d = gains[band]['gain'] * d + gains[band]['offset']

            ## apply mask
            d[nodata] = np.nan

            ## make new data full array
            if ti == 0: data_full = np.zeros(global_dims) + np.nan

            ## add in data
            data_full[offset[1]:offset[1] + d.shape[0], offset[0]:offset[0] + d.shape[1]] = d
            d = None

        ## set up dataset attributes
        ds = 'rhot_{}'.format(waves_names[band])
        if atmospherically_corrected: ds = ds.replace('rhot_', 'rhos_acomp_')

        ds_att = {'wavelength': waves_mu[band] * 1000, 'band_name': band, 'f0': f0_b[band] / 10.}
        if gains != None:
            ds_att['gain'] = gains[band]['gain']
            ds_att['offset'] = gains[band]['offset']
            ds_att['gains_parameter'] = setu['gains_parameter']
        if percentiles_compute:
            ds_att['percentiles'] = percentiles
            ds_att['percentiles_data'] = np.nanpercentile(data_full, percentiles)

        ## write to netcdf file
        if verbosity > 1: print(
            '{} - Converting bands: Writing {} ({})'.format(datetime.datetime.now().isoformat()[0:19], ds,
                                                            data_full.shape))
        gemo.write(ds, data_full, ds_att=ds_att)
        if verbosity > 1: print(
            '{} - Converting bands: Wrote {} ({})'.format(datetime.datetime.now().isoformat()[0:19], ds,
                                                          data_full.shape))
        data_full = None