import time
import numpy as np

from core.atmos.shared import bname_to_slotnum
from core.atmos.run.l2r.ac import percentile_filter, band_data_fixed, band_data_tiled, band_data_segmented
from core.util import fillnan, rsr_convolute_nd

def calculate_aot(band_data:np.ndarray, band_slot:str, var_mem:dict, lut_mod_names:list, b_finite_mask:tuple, left:float, right:float, use_revlut:bool, rev_lut_table:dict, lut_table:dict, ro_type:str, rsrd:dict,
                  gk:str, gk_raa:str, gk_vza:str, is_hyper:bool, user_settings:dict):

    def _load_params():
        aot_fill_nan = user_settings['dsf_aot_fillnan']
        is_tiled = user_settings['dsf_aot_estimate']
        min_tile = user_settings['dsf_min_tile_aot']
        max_tile = user_settings['dsf_max_tile_aot']

        return aot_fill_nan, is_tiled, min_tile, max_tile

    aot_fill_nan, is_tiled, min_tile, max_tile = _load_params()

    aot_band = {}
    for l_i, lut_name in enumerate(lut_mod_names):
        aot_band[lut_name] = np.zeros(band_data.shape, dtype=np.float32) + np.nan
        t0 = time.time()
        band_num = bname_to_slotnum(band_slot)

        ## reverse lut interpolates rhot directly to aot
        if use_revlut:
            if len(rev_lut_table[lut_name]['rgi'][band_num].grid) == 5:
                aot_band[lut_name][b_finite_mask] = rev_lut_table[lut_name]['rgi'][band_num](
                    (var_mem['pressure' + gk][b_finite_mask],
                     var_mem['raa' + gk_raa][b_finite_mask],
                     var_mem['vza' + gk_vza][b_finite_mask],
                     var_mem['sza' + gk][b_finite_mask],
                     band_data[b_finite_mask])
                )
            else:
                aot_band[lut_name][b_finite_mask] = rev_lut_table[lut_name]['rgi'][band_num](
                    (var_mem['pressure' + gk][b_finite_mask],
                     var_mem['raa' + gk_raa][b_finite_mask],
                     var_mem['vza' + gk_vza][b_finite_mask],
                     var_mem['sza' + gk][b_finite_mask],
                     var_mem['wind' + gk][b_finite_mask],
                     band_data[b_finite_mask]))

            # mask out of range aot
            aot_band[lut_name][aot_band[lut_name] <= rev_lut_table[lut_name]['minaot']] = np.nan
            aot_band[lut_name][aot_band[lut_name] >= rev_lut_table[lut_name]['maxaot']] = np.nan

            ## replace nans with closest aot
            if aot_fill_nan:
                aot_band[lut_name] = fillnan(aot_band[lut_name])

        ## standard lut interpolates rhot to results for different aot values
        else:
            ## get rho path for lut steps in aot
            if is_hyper:
                # get modeled rhot for each wavelength
                ## set up array to store modeled rhot
                rhot_aot = np.zeros((len(lut_table[lut_name]['meta']['tau']), \
                                     len(lut_table[lut_name]['meta']['wave']), \
                                     len(var_mem['pressure' + gk].flatten())))

                ## compute rhot for range of aot
                for ai, aot in enumerate(lut_table[lut_name]['meta']['tau']):
                    for pi in range(rhot_aot.shape[2]):
                        tmp = lut_table[lut_name]['rgi']((var_mem['pressure' + gk].flatten()[pi],
                                                          lut_table[lut_name]['ipd'][ro_type],
                                                          lut_table[lut_name]['meta']['wave'],
                                                          var_mem['raa' + gk_raa].flatten()[pi],
                                                          var_mem['vza' + gk_vza].flatten()[pi],
                                                          var_mem['sza' + gk].flatten()[pi],
                                                          var_mem['wind' + gk].flatten()[pi], aot))
                        ## store current result
                        rhot_aot[ai, :, pi] = tmp.flatten()
                # print('Shape of modeled rhot: {}'.format(rhot_aot.shape))

                ## resample modeled results to current band
                tmp = rsr_convolute_nd(rhot_aot, lut_table[lut_name]['meta']['wave'],
                                       rsrd['rsr'][band_num]['response'],
                                       rsrd['rsr'][band_num]['wave'],
                                       axis=1)

                ## interpolate rho path to observation
                aotret = np.zeros(aot_band[lut_name][b_finite_mask].flatten().shape)
                ## interpolate to observed rhot
                for ri, crho in enumerate(band_data.flatten()):
                    aotret[ri] = np.interp(crho, tmp[:, ri], lut_table[lut_name]['meta']['tau'], left=left, right=right)
                # print('Shape of computed aot: {}'.format(aotret.shape))
                aot_band[lut_name][b_finite_mask] = aotret.reshape(aot_band[lut_name][b_finite_mask].shape)
            else:
                if len(var_mem['pressure' + gk]) > 1:
                    for gki in range(len(var_mem['pressure' + gk])):
                        tmp = lut_table[lut_name]['rgi'][band_num]((var_mem['pressure' + gk][gki],
                                                                    lut_table[lut_name]['ipd'][ro_type],
                                                                    var_mem['raa' + gk_raa][gki],
                                                                    var_mem['vza' + gk_vza][gki],
                                                                    var_mem['sza' + gk][gki],
                                                                    var_mem['wind' + gk][gki],
                                                                    lut_table[lut_name]['meta']['tau']))
                        tmp = tmp.flatten()
                        aot_band[lut_name][gki] = np.interp(band_data[gki], tmp, lut_table[lut_name]['meta']['tau'],
                                                            left=left, right=right)
                else:
                    tmp = lut_table[lut_name]['rgi'][band_num]((var_mem['pressure' + gk],
                                                                lut_table[lut_name]['ipd'][ro_type],
                                                                var_mem['raa' + gk_raa],
                                                                var_mem['vza' + gk_vza],
                                                                var_mem['sza' + gk],
                                                                var_mem['wind' + gk],
                                                                lut_table[lut_name]['meta']['tau']))
                    tmp = tmp.flatten()

                    ## interpolate rho path to observation
                    aot_band[lut_name][b_finite_mask] = np.interp(band_data[b_finite_mask], tmp,
                                                                  lut_table[lut_name]['meta']['tau'], left=left,
                                                                  right=right)

        ## mask minimum/maximum tile aots
        if is_tiled == 'tiled':
            aot_band[lut_name][aot_band[lut_name] < min_tile] = np.nan
            aot_band[lut_name][aot_band[lut_name] > max_tile] = np.nan

        # aot_td = time.time() - t0
        # print(f'{global_attrs["sensor"]}/{band_slot} {lut_name} took {tel:.3f}s ({"RevLUT" if use_revlut else "StdLUT"})')

    return aot_band

def calculate_aot_bands(band_table:dict, l1r_band_list:list, rsrd:dict, var_mem:dict, lut_mod_names:list, lut_table:dict, aot_estimate_method:str,
                        use_revlut:bool, rev_lut_table:dict, is_hyper:bool, tiles:list, segment_data:dict, left:float, right:float, ro_type:str, user_settings:dict):
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

    aot_band_list = []
    aot_dict = {}
    dsf_rhod = {}

    for bi, (band_slot, b_v) in enumerate(band_table.items()):
        if band_slot in bandslot_exclude:
            continue
        if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
            continue
        if b_v['att']['rhot_ds'] not in l1r_band_list:
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

        estimated_data = b_v['data'] * 1.0
        valid = np.isfinite(estimated_data) * (estimated_data > 0)
        mask = valid == False

        ## apply TOA filter
        if is_filter_rhot:
            estimated_data = percentile_filter(estimated_data, mask, filter_box, filter_percentile)
        b_finite_mask = np.where(valid)
        del valid, mask

        ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
        gk = ''

        ## fixed path reflectance
        if aot_estimate_method == 'fixed':
            estimated_data, gk = band_data_fixed(estimated_data, b_finite_mask,
                                            percentile, intercept_pixels, spectrum_option)

        ## tiled path reflectance
        elif aot_estimate_method == 'tiled':
            estimated_data, gk = band_data_tiled(estimated_data, tiles,
                                            percentile, intercept_pixels, spectrum_option, min_tile_cover)

        ## image is segmented based on input vector mask
        elif aot_estimate_method == 'segmented':
            estimated_data, gk = band_data_segmented(estimated_data, segment_data,
                                                percentile, intercept_pixels, spectrum_option)

        ## resolved per pixel dsf
        elif aot_estimate_method == 'resolved':
            if not resolved_geometry:
                gk = '_mean'
        else:
            # print(f'DSF option {user_settings["dsf_aot_estimate"]} not configured')
            continue

        del b_finite_mask

        ## do gas correction
        b_finite_mask = np.where(np.isfinite(estimated_data))
        if len(b_finite_mask[0]) > 0:
            estimated_data[b_finite_mask] /= b_v['att']['tt_gas']

        ## store rhod
        if aot_estimate_method in ['fixed', 'tiled', 'segmented']:
            dsf_rhod[band_slot] = estimated_data

        ## use band specific geometry if available
        gk_raa = f'{gk}'
        gk_vza = f'{gk}'
        if f'raa_{b_v["att"]["wave_name"]}' in l1r_band_list:
            gk_raa = f'_{b_v["att"]["wave_name"]}' + gk_raa
        if f'vza_{b_v["att"]["wave_name"]}' in l1r_band_list:
            gk_vza = f'_{b_v["att"]["wave_name"]}' + gk_vza

        ## compute aot

        aot_band = calculate_aot(estimated_data, band_slot, var_mem, lut_mod_names, b_finite_mask, left, right, use_revlut, rev_lut_table, lut_table, ro_type, rsrd,
                                 gk, gk_raa, gk_vza, is_hyper, user_settings)

        ## store current band results
        aot_dict[band_slot] = aot_band
        aot_band_list.append(band_slot)
        del estimated_data, b_finite_mask, aot_band

    return aot_band_list, aot_dict, dsf_rhod, gk