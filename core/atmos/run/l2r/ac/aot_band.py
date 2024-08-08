import time
import numpy as np

from core.atmos.run.l2r.ac import percentile_filter, band_data_fixed, band_data_tiled, band_data_segmented
from core.util import fillnan, rsr_convolute_nd

def calculate_aot(band_data, band_slot:str, data_mem, luts, gk, band_sub, left, right,
                  gk_raa, gk_vza, use_revlut, revl, lutdw, par, rsrd, is_hyper, user_settings):

    def _load_params():
        aot_fill_nan = user_settings['dsf_aot_fillnan']
        is_tiled = user_settings['dsf_aot_estimate']
        min_tile = user_settings['dsf_min_tile_aot']
        max_tile = user_settings['dsf_max_tile_aot']

        return aot_fill_nan, is_tiled, min_tile, max_tile

    aot_fill_nan, is_tiled, min_tile, max_tile = _load_params()

    aot_band = {}
    for l_i, lut_name in enumerate(luts):
        aot_band[lut_name] = np.zeros(band_data.shape, dtype=np.float32) + np.nan
        t0 = time.time()
        band_num = band_slot[1:]

        ## reverse lut interpolates rhot directly to aot
        if use_revlut:
            if len(revl[lut_name]['rgi'][band_num].grid) == 5:
                aot_band[lut_name][band_sub] = revl[lut_name]['rgi'][band_num](
                    (data_mem['pressure' + gk][band_sub],
                     data_mem['raa' + gk_raa][band_sub],
                     data_mem['vza' + gk_vza][band_sub],
                     data_mem['sza' + gk][band_sub],
                     band_data[band_sub])
                )
            else:
                aot_band[lut_name][band_sub] = revl[lut_name]['rgi'][band_num](
                    (data_mem['pressure' + gk][band_sub],
                     data_mem['raa' + gk_raa][band_sub],
                     data_mem['vza' + gk_vza][band_sub],
                     data_mem['sza' + gk][band_sub],
                     data_mem['wind' + gk][band_sub],
                     band_data[band_sub]))

            # mask out of range aot
            aot_band[lut_name][aot_band[lut_name] <= revl[lut_name]['minaot']] = np.nan
            aot_band[lut_name][aot_band[lut_name] >= revl[lut_name]['maxaot']] = np.nan

            ## replace nans with closest aot
            if aot_fill_nan:
                aot_band[lut_name] = fillnan(aot_band[lut_name])

        ## standard lut interpolates rhot to results for different aot values
        else:
            ## get rho path for lut steps in aot
            if is_hyper:
                # get modeled rhot for each wavelength
                ## set up array to store modeled rhot
                rhot_aot = np.zeros((len(lutdw[lut_name]['meta']['tau']), \
                                     len(lutdw[lut_name]['meta']['wave']), \
                                     len(data_mem['pressure' + gk].flatten())))

                ## compute rhot for range of aot
                for ai, aot in enumerate(lutdw[lut_name]['meta']['tau']):
                    for pi in range(rhot_aot.shape[2]):
                        tmp = lutdw[lut_name]['rgi']((data_mem['pressure' + gk].flatten()[pi],
                                                      lutdw[lut_name]['ipd'][par],
                                                      lutdw[lut_name]['meta']['wave'],
                                                      data_mem['raa' + gk_raa].flatten()[pi],
                                                      data_mem['vza' + gk_vza].flatten()[pi],
                                                      data_mem['sza' + gk].flatten()[pi],
                                                      data_mem['wind' + gk].flatten()[pi], aot))
                        ## store current result
                        rhot_aot[ai, :, pi] = tmp.flatten()
                # print('Shape of modeled rhot: {}'.format(rhot_aot.shape))

                ## resample modeled results to current band
                tmp = rsr_convolute_nd(rhot_aot, lutdw[lut_name]['meta']['wave'],
                                                    rsrd['rsr'][band_num]['response'],
                                                    rsrd['rsr'][band_num]['wave'],
                                                    axis=1)

                ## interpolate rho path to observation
                aotret = np.zeros(aot_band[lut_name][band_sub].flatten().shape)
                ## interpolate to observed rhot
                for ri, crho in enumerate(band_data.flatten()):
                    aotret[ri] = np.interp(crho, tmp[:, ri], lutdw[lut_name]['meta']['tau'], left=left, right=right)
                # print('Shape of computed aot: {}'.format(aotret.shape))
                aot_band[lut_name][band_sub] = aotret.reshape(aot_band[lut_name][band_sub].shape)
            else:
                if len(data_mem['pressure' + gk]) > 1:
                    for gki in range(len(data_mem['pressure' + gk])):
                        tmp = lutdw[lut_name]['rgi'][band_num]((data_mem['pressure' + gk][gki],
                                                                lutdw[lut_name]['ipd'][par],
                                                                data_mem['raa' + gk_raa][gki],
                                                                data_mem['vza' + gk_vza][gki],
                                                                data_mem['sza' + gk][gki],
                                                                data_mem['wind' + gk][gki],
                                                                lutdw[lut_name]['meta']['tau']))
                        tmp = tmp.flatten()
                        aot_band[lut_name][gki] = np.interp(band_data[gki], tmp, lutdw[lut_name]['meta']['tau'],
                                                            left=left, right=right)
                else:
                    tmp = lutdw[lut_name]['rgi'][band_num]((data_mem['pressure' + gk],
                                                            lutdw[lut_name]['ipd'][par],
                                                            data_mem['raa' + gk_raa],
                                                            data_mem['vza' + gk_vza],
                                                            data_mem['sza' + gk],
                                                            data_mem['wind' + gk],
                                                            lutdw[lut_name]['meta']['tau']))
                    tmp = tmp.flatten()

                    ## interpolate rho path to observation
                    aot_band[lut_name][band_sub] = np.interp(band_data[band_sub], tmp,
                                                             lutdw[lut_name]['meta']['tau'], left=left,
                                                             right=right)

        ## mask minimum/maximum tile aots
        if is_tiled == 'tiled':
            aot_band[lut_name][aot_band[lut_name] < min_tile] = np.nan
            aot_band[lut_name][aot_band[lut_name] > max_tile] = np.nan

        aot_td = time.time() - t0
        # print(f'{global_attrs["sensor"]}/{band_slot} {lut_name} took {tel:.3f}s ({"RevLUT" if use_revlut else "StdLUT"})')

    return aot_band

def calculate_aot_bands(band_ds, l1r_ds, rsrd, data_mem, luts, lutdw, aot_estimate_method, use_revlut, revl, is_hyper, tiles, segment_data, left, right, user_settings):
    def _load_params():
        percentile = user_settings['dsf_percentile']
        intercept_pixels = user_settings['dsf_intercept_pixels']
        spectrum_option = user_settings['dsf_spectrum_option']
        bandslot_exclude = user_settings['dsf_exclude_bands']
        is_filter_rhot = user_settings['dsf_filter_rhot']
        min_gas = user_settings['min_tgas_aot']
        wave_range = user_settings['dsf_wave_range']
        filter_box = user_settings['dsf_filter_box']
        filter_percentile = user_settings['dsf_filter_percentile']
        min_tile_cover = user_settings['dsf_min_tile_cover']
        resolved_geometry = user_settings['resolved_geometry']

        return percentile, intercept_pixels, spectrum_option, bandslot_exclude, \
            is_filter_rhot, min_gas, wave_range, filter_box, filter_percentile, min_tile_cover, resolved_geometry

    percentile, intercept_pixels, spectrum_option, bandslot_exclude, is_filter_rhot, \
        min_gas, wave_range, filter_box, filter_percentile, min_tile_cover, resolved_geometry = _load_params()

    aot_bands = []
    aot_dict = {}
    dsf_rhod = {}

    for bi, (band_slot, b_v) in enumerate(band_ds.items()):
        if band_slot in bandslot_exclude:
            continue
        if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
            continue
        if b_v['att']['rhot_ds'] not in l1r_ds:
            continue

        ## skip band for aot computation
        if b_v['att']['tt_gas'] < min_gas:
            continue

        ## skip bands according to configuration
        if (b_v['att']['wave_nm'] < wave_range[0]):
            continue
        if (b_v['att']['wave_nm'] > wave_range[1]):
            continue

        # print(band_slot, b_v['att']['rhot_ds'])

        band_data = b_v['data'] * 1.0
        valid = np.isfinite(band_data) * (band_data > 0)
        mask = valid == False

        ## apply TOA filter
        if is_filter_rhot:
            band_data = percentile_filter(band_data, mask, filter_box, filter_percentile)
        band_sub = np.where(valid)
        del valid, mask

        ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
        gk = ''

        ## fixed path reflectance
        if aot_estimate_method == 'fixed':
            band_data, gk = band_data_fixed(band_data, band_sub,
                                            percentile, intercept_pixels, spectrum_option)

        ## tiled path reflectance
        elif aot_estimate_method == 'tiled':
            band_data, gk = band_data_tiled(band_data, tiles,
                                            percentile, intercept_pixels, spectrum_option, min_tile_cover)

        ## image is segmented based on input vector mask
        elif aot_estimate_method == 'segmented':
            band_data, gk = band_data_segmented(band_data, segment_data,
                                                percentile, intercept_pixels, spectrum_option)

        ## resolved per pixel dsf
        elif aot_estimate_method == 'resolved':
            if not resolved_geometry:
                gk = '_mean'
        else:
            # print(f'DSF option {user_settings["dsf_aot_estimate"]} not configured')
            continue

        del band_sub

        ## do gas correction
        band_sub = np.where(np.isfinite(band_data))
        if len(band_sub[0]) > 0:
            band_data[band_sub] /= b_v['att']['tt_gas']

        ## store rhod
        if aot_estimate_method in ['fixed', 'tiled', 'segmented']:
            dsf_rhod[band_slot] = band_data

        ## use band specific geometry if available
        gk_raa = f'{gk}'
        gk_vza = f'{gk}'
        if f'raa_{b_v["att"]["wave_name"]}' in l1r_ds:
            gk_raa = f'_{b_v["att"]["wave_name"]}' + gk_raa
        if f'vza_{b_v["att"]["wave_name"]}' in l1r_ds:
            gk_vza = f'_{b_v["att"]["wave_name"]}' + gk_vza

        ## compute aot

        aot_band = calculate_aot(band_data, band_slot, data_mem, luts, gk, band_sub, left, right,
                                 gk_raa, gk_vza, use_revlut, revl, lutdw, b_v['att']['par'], rsrd,
                                 is_hyper, user_settings)

        ## store current band results
        aot_dict[band_slot] = aot_band
        aot_bands.append(band_slot)
        del band_data, band_sub, aot_band

    return aot_dict, aot_bands, dsf_rhod, gk