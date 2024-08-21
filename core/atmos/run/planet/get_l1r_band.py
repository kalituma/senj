import numpy as np
import json

def get_l1r_band(bands:dict, band_indices:dict, tif_meta:dict, f0_dict:dict, sensor:str,
                 se_distance:float, mus:float, waves_names:dict, waves_mu:dict, value_conversion:dict,
                 gains:bool, gains_dict:dict, percentiles_compute:bool, percentiles:list,
                 from_radiance=False):
    out = {}
    for band_name, band in bands.items():
        band_slot = band['slot']
        d = band['value'].copy()
        idx = int(band_indices[f'{band_slot}-band_idx'])
        if band_slot in ['PAN']:
            continue

        nodata = d == np.uint16(0)

        if 'Skysat' in sensor:
            ## get reflectance scaling from tiff tags
            try:
                prop = json.loads(tif_meta['TIFFTAG_IMAGEDESCRIPTION'])['properties']
            except:
                prop = {}

            if 'reflectance_coefficients' in prop:
                ## convert to toa radiance & mask
                bi = idx - 1
                d = d.astype(float) * prop['reflectance_coefficients'][bi]
                d[nodata] = np.nan
            else:
                # print('Using fixed 0.01 factor to convert Skysat DN to TOA radiance')
                ## convert to toa radiance & mask
                d = d.astype(float) * 0.01

                ## convert to toa reflectance
                f0 = f0_dict[band_slot] / 10
                d *= (np.pi * se_distance ** 2) / (f0 * mus)
        else:
            ## convert from radiance
            if sensor == 'RapidEye' or from_radiance:
                d = d.astype(float) * float(value_conversion[f'{band_slot}-{"to_radiance"}'])
                f0 = f0_dict[band_slot] / 10
                d *= (np.pi * se_distance ** 2) / (f0 * mus)
            else:
                d = d.astype(float) * float(value_conversion[f'{band_slot}-{"to_reflectance"}'])

        d[nodata] = np.nan

        ds = f'rhot_{waves_names[band_slot]}'
        l1r_band_attr = {'wavelength': waves_mu[band_slot] * 1000, 'band_slot': band_slot, 'parameter': ds}

        if gains and gains_dict is not None:
            l1r_band_attr['toa_gain'] = gains_dict[band_slot]
            d *= l1r_band_attr['toa_gain']
            # if verbosity > 1: print('Converting bands: Applied TOA gain {} to {}'.format(ds_att['toa_gain'], ds))

        if percentiles_compute:
            l1r_band_attr['percentiles'] = percentiles
            l1r_band_attr['percentiles_data'] = np.nanpercentile(d, percentiles)

        out[band_slot] = {
            'data': d,
            'att': l1r_band_attr
        }

    return out