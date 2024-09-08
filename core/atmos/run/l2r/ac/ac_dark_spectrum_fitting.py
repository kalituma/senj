import numpy as np
import scipy.ndimage, scipy.interpolate

import core.atmos as atmos
from core.util import rsr_convolute_nd, Logger
from core.atmos.shared import bname_to_slotnum
from core.atmos.run.l2r.ac.aot_band import calculate_aot_bands

def apply_dsf(band_table:dict, var_mem:dict, lut_table:dict, rsrd:dict, lut_mod_names:list, l1r_band_list:list, ro_type:str, user_settings:dict, use_rev_lut:bool,
              rev_lut_table:dict=None, tiles:list=None, segment_data:dict=None, is_hyper:bool=False):

    def _load_params():
        aot_estimate_method = user_settings['dsf_aot_estimate'] # fixed, tiled, segmented
        spectrum_option = user_settings['dsf_spectrum_option'] # 'darkest', 'percentile', 'intercept'
        allow_lut_boundaries = user_settings['dsf_allow_lut_boundaries']
        fixed_aot = user_settings['dsf_fixed_aot']
        nbands = user_settings['dsf_nbands']
        nbands_fit = user_settings['dsf_nbands_fit']
        aot_compute = user_settings['dsf_aot_compute']
        filter_aot = user_settings['dsf_filter_aot']
        smooth_aot = user_settings['dsf_smooth_aot']
        model_selection_method = user_settings['dsf_model_selection']
        most_common_model = user_settings['dsf_aot_most_common_model']

        return aot_estimate_method, spectrum_option, allow_lut_boundaries, fixed_aot, \
            nbands, nbands_fit, aot_compute, filter_aot, smooth_aot, model_selection_method, most_common_model

    aot_estimate_method, spectrum_option, allow_lut_boundaries, fixed_aot, nbands, nbands_fit, aot_compute, \
        filter_aot, smooth_aot, model_selection_method, most_common_model = _load_params()

    ## #####################
    ## dark spectrum fitting
    aot_lut = None
    aot_sel = None
    aot_sel_lut = None
    aot_sel_par = None
    aot_stack = None
    aot_sel_bands = None

    left, right = np.nan, np.nan
    if allow_lut_boundaries:
        left, right = None, None

    ## user supplied aot
    if fixed_aot is not None:
        aot_estimate_method = 'fixed'
        aot_lut = None
        for l_i, lut_name in enumerate(lut_mod_names):
            if lut_name == fixed_aot:
                aot_lut = np.array(l_i)
                aot_lut.shape += (1, 1)  ## make 1,1 dimensions
        if aot_lut is None:
            Logger.get_logger().log('error', f'LUT {fixed_aot} not recognised')

        aot_sel = np.array(float(fixed_aot))
        aot_sel.shape += (1, 1)  ## make 1,1 dimensions
        aot_sel_lut = lut_mod_names[aot_lut[0][0]]
        aot_sel_par = None
        Logger.get_logger().log('info', f'User specified aot {aot_sel[0][0]} and model {aot_sel_lut}')

        ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
        gk = '' if use_rev_lut else '_mean'

    ## image derived aot
    else:
        if spectrum_option not in ['darkest', 'percentile', 'intercept']:
            Logger.get_logger().log('error', f'dsf_spectrum_option {spectrum_option} not configured, falling back to darkest')
            user_settings['dsf_spectrum_option'] = 'darkest'

        ## run through bands to get aot
        aot_bands, aot_dict, dsf_rhod, gk = calculate_aot_bands(band_table, l1r_band_list, rsrd, var_mem, lut_mod_names=lut_mod_names, lut_table=lut_table, aot_estimate_method=aot_estimate_method,
                                                                use_revlut=use_rev_lut, rev_lut_table=rev_lut_table, is_hyper=is_hyper, tiles=tiles, segment_data=segment_data,
                                                                left=left, right=right, ro_type=ro_type, user_settings=user_settings)
        ## get min aot per pixel
        aot_stack = {}
        for l_i, lut_name in enumerate(lut_mod_names):
            aot_band_list = []
            ## stack aot for this lut
            for bi, band_slot in enumerate(aot_bands):
                if band_slot not in aot_dict:
                    continue
                aot_band_list.append(band_slot)
                if lut_name not in aot_stack:
                    aot_stack[lut_name] = {'all': aot_dict[band_slot][lut_name] * 1.0}
                else:
                    aot_stack[lut_name]['all'] = np.dstack((aot_stack[lut_name]['all'],
                                                            aot_dict[band_slot][lut_name]))
            aot_stack[lut_name]['band_list'] = aot_band_list

            ## get highest aot per pixel for all bands
            tmp = np.argsort(aot_stack[lut_name]['all'], axis=2)
            ay, ax = np.meshgrid(np.arange(tmp.shape[1]), np.arange(tmp.shape[0]))

            ## identify number of bands
            if nbands < 2:
                nbands = user_settings['dsf_nbands'] = 2
            if nbands > tmp.shape[2]:
                nbands = user_settings['dsf_nbands'] = tmp.shape[2]
            if nbands_fit < 2:
                nbands_fit = user_settings['dsf_nbands_fit'] = 2
            if nbands_fit > tmp.shape[2]:
                nbands_fit = user_settings['dsf_nbands_fit'] = tmp.shape[2]

            ## get minimum or average aot
            if aot_compute in ['mean', 'median']:
                Logger.get_logger().log('info', f'Using dsf_aot_compute = {user_settings["dsf_aot_compute"]}')

                ## stack n lowest bands
                for ai in range(nbands):
                    if ai == 0:
                        # find aot at 1st order
                        tmp_aot = aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, ai]] * 1.0
                    else:
                        # find aot at 2nd order
                        tmp_aot = np.dstack((tmp_aot, aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, ai]] * 1.0))

                ## compute mean over stack
                if aot_compute == 'mean':
                    aot_stack[lut_name]['aot'] = np.nanmean(tmp_aot, axis=2)
                if aot_compute == 'median':
                    aot_stack[lut_name]['aot'] = np.nanmedian(tmp_aot, axis=2)
                if aot_estimate_method == 'fixed':
                    Logger.get_logger().log('info', f'Using dsf_aot_compute = {user_settings["dsf_aot_compute"]} {lut_name} aot = {float(aot_stack[lut_name]["aot"].flatten()):.3f}')
                tmp_aot = None
            else:
                aot_stack[lut_name]['aot'] = aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, 0]]  # np.nanmin(aot_stack[lut]['all'], axis=2)

            ## if minimum for fixed retrieval is nan, set it to 0.01
            if aot_estimate_method == 'fixed':
                if np.isnan(aot_stack[lut_name]['aot']):
                    aot_stack[lut_name]['aot'][0][0] = 0.01
            aot_stack[lut_name]['mask'] = ~np.isfinite(aot_stack[lut_name]['aot'])

            if aot_estimate_method == 'resolved':
                ## apply percentile filter
                if filter_aot:
                    filter_percentile = user_settings['dsf_filter_percentile']
                    filter_box = user_settings['dsf_filter_box']
                    aot_stack[lut_name]['aot'] = scipy.ndimage.percentile_filter(aot_stack[lut_name]['aot'], filter_percentile, size=filter_box)
                ## apply gaussian kernel smoothing
                if smooth_aot:
                    ## for gaussian smoothing of aot
                    smooth_box = user_settings['dsf_smooth_box']
                    aot_stack[lut_name]['aot'] = scipy.ndimage.gaussian_filter(aot_stack[lut_name]['aot'], smooth_box, order=0, mode='nearest')

            ## mask aot
            aot_stack[lut_name]['aot'][aot_stack[lut_name]['mask']] = np.nan

            ## store bands for fitting rmsd
            for bbi in range(nbands_fit):
                aot_stack[lut_name][f'b{bbi + 1}'] = tmp[:, :, bbi].astype(int)  # .astype(float)
                aot_stack[lut_name][f'b{bbi + 1}'][aot_stack[lut_name]['mask']] = -1

            if model_selection_method == 'min_dtau':
                ## array idices
                aid = np.indices(aot_stack[lut_name]['all'].shape[0:2])
                ## abs difference between first and second band tau
                aot_stack[lut_name]['dtau'] = np.abs(aot_stack[lut_name]['all'][aid[0, :], aid[1, :], tmp[:, :, 0]] - aot_stack[lut_name]['all'][aid[0, :], aid[1, :], tmp[:, :, 1]])

            ## remove sorted indices
            tmp = None
        ## select model based on min rmsd for 2 bands
        Logger.get_logger().log('info', f'Choosing best fitting model: {user_settings["dsf_model_selection"]} ({user_settings["dsf_nbands"]} bands)')

        ## run through model results, get rhod and rhop for n lowest bands
        for l_i, lut_name in enumerate(lut_mod_names):
            ## select model based on minimum rmsd between n best fitting bands
            if model_selection_method == 'min_drmsd':

                Logger.get_logger().log('info', f'Computing RMSD for model {lut_name}')
                rhop_f = np.zeros((aot_stack[lut_name]['b1'].shape[0], aot_stack[lut_name]['b1'].shape[1], nbands_fit), dtype=np.float32) + np.nan
                rhod_f = np.zeros((aot_stack[lut_name]['b1'].shape[0], aot_stack[lut_name]['b1'].shape[1], nbands_fit),dtype=np.float32) + np.nan

                for bi, band_slot in enumerate(aot_bands):
                    band_num = bname_to_slotnum(band_slot)

                    ## use band specific geometry if available
                    gk_raa = gk
                    gk_vza = gk
                    if f'raa_{band_table[band_slot]["att"]["wave_name"]}' in l1r_band_list:
                        gk_raa = f'_{band_table[band_slot]["att"]["wave_name"]}' + gk_raa
                    if f'vza_{band_table[band_slot]["att"]["wave_name"]}' in l1r_band_list:
                        gk_vza = f'_{band_table[band_slot]["att"]["wave_name"]}' + gk_vza

                    ## run through two best fitting bands
                    fit_bands = [f'b{bbi + 1}' for bbi in range(nbands_fit)]
                    for ai, ab in enumerate(fit_bands):
                        aot_loc = np.where(aot_stack[lut_name][ab] == bi)
                        ## get rhod for current band
                        if aot_estimate_method == 'resolved':
                            rhod_f[aot_loc[0], aot_loc[1], ai] = band_table[band_slot]['data'][aot_loc]
                        elif aot_estimate_method == 'segmented':
                            rhod_f[aot_loc[0], aot_loc[1], ai] = dsf_rhod[band_slot][aot_loc].flatten()
                        else:
                            rhod_f[aot_loc[0], aot_loc[1], ai] = dsf_rhod[band_slot][aot_loc]  # band_data / gas
                        ## get rho path for current band
                        if len(aot_loc[0]) > 0:
                            if use_rev_lut:
                                xi = [var_mem['pressure' + gk][aot_loc], var_mem['raa' + gk_raa][aot_loc], var_mem['vza' + gk_vza][aot_loc], var_mem['sza' + gk][aot_loc], var_mem['wind' + gk][aot_loc]]
                            else:
                                xi = [var_mem['pressure' + gk], var_mem['raa' + gk_raa], var_mem['vza' + gk_vza], var_mem['sza' + gk], var_mem['wind' + gk]]

                            if is_hyper:
                                ## get hyperspectral results and resample to band
                                if len(aot_stack[lut_name]['aot'][aot_loc]) == 1:
                                    if len(xi[0]) == 0:
                                        res_hyp = lut_table[lut_name]['rgi']((xi[0], lut_table[lut_name]['ipd'][ro_type], lut_table[lut_name]['meta']['wave'], xi[1], xi[2], xi[3], xi[4], aot_stack[lut_name]['aot'][aot_loc]))
                                    else:  ## if more resolved geometry
                                        res_hyp = lut_table[lut_name]['rgi']((xi[0][aot_loc], lut_table[lut_name]['ipd'][ro_type], lut_table[lut_name]['meta']['wave'], xi[1][aot_loc], xi[2][aot_loc], xi[3][aot_loc], xi[4][aot_loc], aot_stack[lut_name]['aot'][aot_loc]))
                                    rhop_f[aot_loc[0], aot_loc[1], ai] = rsr_convolute_nd(res_hyp.flatten(), lut_table[lut_name]['meta']['wave'], rsrd['rsr'][band_slot]['response'], rsrd['rsr'][band_slot]['wave'], axis=0)
                                else:
                                    for iii in range(len(aot_stack[lut_name]['aot'][aot_loc])):
                                        if len(xi[0]) == 0:
                                            res_hyp = lut_table[lut_name]['rgi']((xi[0], lut_table[lut_name]['ipd'][ro_type], lut_table[lut_name]['meta']['wave'], xi[1], xi[2], xi[3], xi[4], aot_stack[lut_name]['aot'][aot_loc][iii]))

                                        else:  ## if more resolved geometry
                                            res_hyp = lut_table[lut_name]['rgi']((xi[0].flatten()[iii], lut_table[lut_name]['ipd'][ro_type], lut_table[lut_name]['meta']['wave'],
                                                                                  xi[1].flatten()[iii], xi[2].flatten()[iii], xi[3].flatten()[iii], xi[4].flatten()[iii], aot_stack[lut_name]['aot'][aot_loc][iii]))
                                        rhop_f[aot_loc[0][iii], aot_loc[1][iii], ai] = rsr_convolute_nd(res_hyp.flatten(),
                                                                                                        lut_table[lut_name]['meta']['wave'],
                                                                                                        rsrd['rsr'][band_slot]['response'],
                                                                                                        rsrd['rsr'][band_slot]['wave'],
                                                                                                        axis=0)
                            else:
                                if aot_estimate_method == 'segmented':
                                    for gki in range(len(aot_loc[0])):
                                        rhop_f[aot_loc[0][gki], aot_loc[1][gki], ai] = lut_table[lut_name]['rgi'][band_num](
                                            (xi[0][aot_loc[0][gki]], lut_table[lut_name]['ipd'][ro_type],
                                             xi[1][aot_loc[0][gki]], xi[2][aot_loc[0][gki]],
                                             xi[3][aot_loc[0][gki]], xi[4][aot_loc[0][gki]],
                                             aot_stack[lut_name]['aot'][aot_loc][gki])
                                        )

                                else:
                                    rhop_f[aot_loc[0], aot_loc[1], ai] = lut_table[lut_name]['rgi'][band_num](
                                        (xi[0], lut_table[lut_name]['ipd'][ro_type], xi[1], xi[2], xi[3], xi[4],
                                         aot_stack[lut_name]['aot'][aot_loc])
                                    )

                ## rmsd for current bands
                cur_sel_par = np.sqrt(np.nanmean(np.square((rhod_f - rhop_f)), axis=2))  # band_data - lut value for aot to trans
                if (aot_estimate_method == 'fixed'):
                    Logger.get_logger().log('info', f'Computing RMSD for model {lut_name}: {cur_sel_par[0][0]:.4e}')

            ## end select with min RMSD

            ## select model based on minimum delta tau between two lowest aot bands
            if model_selection_method == 'min_dtau':
                cur_sel_par = aot_stack[lut_name]['dtau']
            ## end select with min delta tau

            ## store minimum info
            if l_i == 0:
                aot_lut = np.zeros(aot_stack[lut_name]['aot'].shape, dtype=np.float32).astype(int)
                aot_lut[aot_stack[lut_name]['mask']] = -1
                aot_sel = aot_stack[lut_name]['aot'] * 1.0
                aot_sel_par = cur_sel_par * 1.0
                if aot_estimate_method == 'fixed':
                    aot_sel_lut = f'{lut_name}'
                    aot_sel_bands = [aot_stack[lut_name][f'{bb}'][0][0] for bb in fit_bands]
            else:
                aot_loc = np.where(cur_sel_par < aot_sel_par)
                if len(aot_loc[0]) == 0:
                    continue
                aot_lut[aot_loc] = l_i
                aot_sel[aot_loc] = aot_stack[lut_name]['aot'][aot_loc] * 1.0
                aot_sel_par[aot_loc] = cur_sel_par[aot_loc] * 1.0
                if aot_estimate_method == 'fixed':
                    aot_sel_lut = f'{lut_name}'
                    aot_sel_bands = [aot_stack[lut_name][f'{bb}'][0][0] for bb in fit_bands]

        rhod_f = None
        rhod_p = None

    if aot_estimate_method == 'fixed' and aot_sel_par is not None:
        Logger.get_logger().log('info', f'Selected model {aot_sel_lut}: aot {aot_sel[0][0]:.3f}, RMSD {aot_sel_par[0][0]:.2e}')

    ## check variable aot, use most common LUT
    if aot_estimate_method != 'fixed' and most_common_model:
        Logger.get_logger().log('info', 'Selecting most common model for processing.')
        n_aot = len(np.where(aot_lut != -1)[0])  # 0 = mod_1, 1 = mod2, -1 = null
        n_sel = 0
        for l_i, lut_name in enumerate(lut_mod_names):
            sub = np.where(aot_lut == l_i)  # get indices where mod type is equal with current mod number
            n_cur = len(sub[0])
            if n_cur == 0:
                Logger.get_logger().log('info', f'{lut_name}: {0:.1f}%')
            else:
                Logger.get_logger().log('info', f'{lut_name}: {100 * n_cur / n_aot:.1f}%: mean aot of subset = {np.nanmean(aot_sel[sub]):.2f}')
            if n_cur >= n_sel:
                n_sel = n_cur
                li_sel = l_i
                aot_sel_lut = f'{lut_name}'
        ## set selected model
        aot_lut[:] = li_sel
        aot_sel[:] = aot_stack[aot_sel_lut]['aot'][:] * 1.0
        aot_sel_par[:] = np.nan  # to do
        Logger.get_logger().log('info', f'Selected {aot_sel_lut}, mean aot = {np.nanmean(aot_sel):.2f}')
    ### end dark_spectrum_fitting

    return aot_lut, aot_sel, aot_stack, aot_sel_par, aot_sel_bands, gk