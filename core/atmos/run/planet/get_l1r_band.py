
def get_l1r_band(bands:dict, rsr_bands:list):
    ## convert bands TOA
    for b in rsr_bands:
        if b in ['PAN']:
            continue
        idx = int(meta_dict[f'{b}-band_idx'])

        ## read data
        md, data = ac.shared.read_band(image_file, idx=idx, warp_to=warp_to, gdal_meta=True)
        nodata = data == np.uint16(0)

        if 'Skysat' in meta_dict['sensor']:
            ## get reflectance scaling from tiff tags
            try:
                prop = json.loads(md['TIFFTAG_IMAGEDESCRIPTION'])['properties']
            except:
                prop = {}

            if 'reflectance_coefficients' in prop:
                ## convert to toa radiance & mask
                bi = idx - 1
                data = data.astype(float) * prop['reflectance_coefficients'][bi]
                data[nodata] = np.nan
            else:
                # print('Using fixed 0.01 factor to convert Skysat DN to TOA radiance')
                ## convert to toa radiance & mask
                data = data.astype(float) * 0.01

                ## convert to toa reflectance
                f0 = global_attrs[f'{b}_f0'] / 10
                data *= (np.pi * global_attrs['se_distance'] ** 2) / (f0 * global_attrs['mus'])
        else:
            ## convert from radiance
            if meta_dict['sensor'] == 'RapidEye' or from_radiance:
                data = data.astype(float) * float(meta_dict[f'{b}-{"to_radiance"}'])
                f0 = global_attrs[f'{b}_f0'] / 10
                data *= (np.pi * global_attrs['se_distance'] ** 2) / (f0 * global_attrs['mus'])
            else:
                data = data.astype(float) * float(meta_dict[f'{b}-{"to_reflectance"}'])

        data[nodata] = np.nan

        band_name = 'rhot_{}'.format(waves_names[b])
        band_att = {'wavelength': waves_mu[b] * 1000}

        if gains & (gains_dict is not None):
            band_att['toa_gain'] = gains_dict[b]
            data *= band_att['toa_gain']
            # if verbosity > 1: print('Converting bands: Applied TOA gain {} to {}'.format(ds_att['toa_gain'], ds))

        if percentiles_compute:
            band_att['percentiles'] = percentiles
            band_att['percentiles_data'] = np.nanpercentile(data, percentiles)

        ## write to netcdf file
        # bands[band_name] = {
        #     data, ds_att=ds_att, replace_nan=True
        # }

        # if verbosity > 1: print('Converting bands: Wrote {} ({})'.format(ds, data.shape))