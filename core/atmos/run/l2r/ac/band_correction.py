import numpy as np
from core.util import rsr_convolute_nd, tiles_interp

def exp_correction(b_dict, b_data, b_num,
                   lut_table, ro_type, rhoam, xi, exp_lut, short_wv, long_wv, epsilon, mask, fixed_epsilon, fixed_rhoam):

    ## get Rayleigh correction
    rorayl_cur = lut_table[exp_lut]['rgi'][b_num]((xi[0], lut_table[exp_lut]['ipd'][ro_type], xi[1], xi[2], xi[3], xi[4], 0.001))
    dutotr_cur = lut_table[exp_lut]['rgi'][b_num]((xi[0], lut_table[exp_lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], 0.001))

    ## get epsilon in current band
    delta = (long_wv - b_dict['att']['wave_nm']) / (long_wv - short_wv)
    eps_cur = np.power(epsilon, delta)
    rhoam_cur = rhoam * eps_cur

    ## add results to band
    if fixed_epsilon:
        b_dict['att']['epsilon'] = eps_cur
    if fixed_rhoam:
        b_dict['att']['rhoam'] = rhoam_cur

    b_data = (b_data - rorayl_cur - rhoam_cur) / (dutotr_cur)
    b_data[mask] = np.nan
    ## end exponential

    return b_data, rorayl_cur, dutotr_cur

def dsf_correction(b_dict, b_data, b_slot:str, b_num:str, xnew:np.ndarray, ynew:np.ndarray, l1r_band_list:list, hyper_res:dict, ttot_all:dict,
                   aot_sel:np.ndarray, aot_lut:np.ndarray, rsrd:dict, lut_mod_names:list, lut_table:dict, var_mem:dict,
                   segment_data:dict, use_revlut:bool, gk:str, gk_vza:str, gk_raa:str, ro_type:str, is_hyper:bool, user_settings:dict, global_attrs:dict,
                   l2r:dict):

    def _load_params():
        slicing = user_settings['slicing']
        aot_estimate = user_settings['dsf_aot_estimate']
        residual_glint_correction = user_settings['dsf_residual_glint_correction']
        residual_glint_correction_method = user_settings['dsf_residual_glint_correction_method']
        tile_smoothing = user_settings['dsf_tile_smoothing']
        tile_smoothing_kernel_size = user_settings['dsf_tile_smoothing_kernel_size']
        tile_interp_method = user_settings['dsf_tile_interp_method']

        return slicing, aot_estimate, residual_glint_correction, residual_glint_correction_method, tile_smoothing, tile_smoothing_kernel_size, tile_interp_method

    slicing, aot_estimate, glint_correction, glint_correction_method, tile_smoothing, tile_smoothing_kernel_size, tile_interp_method = _load_params()



    valid_mask = None
    if slicing:
        valid_mask = np.isfinite(b_data)

    ## shape of atmospheric datasets
    atm_shape = aot_sel.shape

    ## if path reflectance is resolved, but resolved geometry available
    if use_revlut and aot_estimate == 'fixed':
        atm_shape = b_data.shape

    ## use band specific geometry if available
    if f'raa_{b_dict["att"]["wave_name"]}' in l1r_band_list:
        gk_raa = f'_{b_dict["att"]["wave_name"]}' + gk_raa
    if 'vza_{}'.format(b_dict["att"]["wave_name"]) in l1r_band_list:
        gk_vza = f'_{b_dict["att"]["wave_name"]}' + gk_vza

    romix = np.zeros(atm_shape, dtype=np.float32) + np.nan
    astot = np.zeros(atm_shape, dtype=np.float32) + np.nan
    dutott = np.zeros(atm_shape, dtype=np.float32) + np.nan

    if glint_correction and glint_correction_method == 'default':
        ttot_all[b_slot] = np.zeros(atm_shape, dtype=np.float32) + np.nan

    for li, lut_name in enumerate(lut_mod_names):
        aot_loc = np.where(aot_lut == li)
        if len(aot_loc[0]) == 0:
            continue
        aot_vals = aot_sel[aot_loc]

        ## resolved geometry with fixed path reflectance
        if use_revlut and aot_estimate == 'fixed':
            aot_loc = np.where(b_data)

        if use_revlut:
            xi = [var_mem['pressure' + gk][aot_loc], var_mem['raa' + gk_raa][aot_loc], var_mem['vza' + gk_vza][aot_loc], var_mem['sza' + gk][aot_loc], var_mem['wind' + gk][aot_loc]]
        else:
            xi = [var_mem['pressure' + gk], var_mem['raa' + gk_raa], var_mem['vza' + gk_vza], var_mem['sza' + gk], var_mem['wind' + gk]]
            # subset to number of estimates made for this LUT
            ## QV 2022-07-28 maybe not needed any more?
            # if len(xi[0]) > 1:
            #    xi = [[x[l] for l in ls[0]] for x in xi]

        if is_hyper:
            ## compute hyper results and resample later
            if hyper_res is None:
                hyper_res = {}
                for prm in [ro_type, 'astot', 'dutott', 'ttot']:
                    if len(aot_vals) == 1:  ## fixed DSF
                        hyper_res[prm] = lut_table[lut_name]['rgi']((xi[0], lut_table[lut_name]['ipd'][prm],
                                                                lut_table[lut_name]['meta']['wave'], xi[1], xi[2], xi[3],
                                                                xi[4], aot_vals)).flatten()
                    else:  ## tiled/resolved DSF
                        hyper_res[prm] = np.zeros((len(lut_table[lut_name]['meta']['wave']), len(aot_vals))) + np.nan
                        for iii in range(len(aot_vals)):
                            if len(xi[0]) == 1:
                                hyper_res[prm][:, iii] = lut_table[lut_name]['rgi']((xi[0], lut_table[lut_name]['ipd'][prm],
                                                                                lut_table[lut_name]['meta']['wave'], xi[1],
                                                                                xi[2], xi[3], xi[4],
                                                                                aot_vals[iii])).flatten()
                            else:
                                hyper_res[prm][:, iii] = lut_table[lut_name]['rgi'](
                                    (xi[0].flatten()[iii], lut_table[lut_name]['ipd'][prm],
                                     lut_table[lut_name]['meta']['wave'], xi[1].flatten()[iii], xi[2].flatten()[iii],
                                     xi[3].flatten()[iii], xi[4].flatten()[iii], aot_vals[iii])).flatten()

            ## resample to current band
            ### path reflectance
            romix[aot_loc] = rsr_convolute_nd(hyper_res[ro_type], lut_table[lut_name]['meta']['wave'],
                                         rsrd['rsr'][b_num]['response'],
                                         rsrd['rsr'][b_num]['wave'], axis=0)
            ## transmittance and spherical albedo
            astot[aot_loc] = rsr_convolute_nd(hyper_res['astot'], lut_table[lut_name]['meta']['wave'],
                                         rsrd['rsr'][b_num]['response'],
                                         rsrd['rsr'][b_num]['wave'], axis=0)
            dutott[aot_loc] = rsr_convolute_nd(hyper_res['dutott'], lut_table[lut_name]['meta']['wave'],
                                          rsrd['rsr'][b_num]['response'],
                                          rsrd['rsr'][b_num]['wave'], axis=0)

            ## total transmittance
            if glint_correction and glint_correction_method == 'default':
                ttot_all[b_slot][aot_loc] = rsr_convolute_nd(hyper_res['ttot'], lut_table[lut_name]['meta']['wave'],
                                                        rsrd['rsr'][b_num]['response'],
                                                        rsrd['rsr'][b_num]['wave'],
                                                        axis=0)
        else:
            ## path reflectance
            romix[aot_loc] = lut_table[lut_name]['rgi'][b_num]((xi[0], lut_table[lut_name]['ipd'][ro_type], xi[1], xi[2], xi[3], xi[4], aot_vals))

            ## transmittance and spherical albedo
            astot[aot_loc] = lut_table[lut_name]['rgi'][b_num]((xi[0], lut_table[lut_name]['ipd']['astot'], xi[1], xi[2], xi[3], xi[4], aot_vals))
            dutott[aot_loc] = lut_table[lut_name]['rgi'][b_num]((xi[0], lut_table[lut_name]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], aot_vals))

            ## total transmittance
            if glint_correction and glint_correction_method == 'default':
                ttot_all[b_slot][aot_loc] = lut_table[lut_name]['rgi'][b_num]((xi[0], lut_table[lut_name]['ipd']['ttot'], xi[1], xi[2], xi[3], xi[4], aot_vals))
        del aot_loc, aot_vals, xi

    ## interpolate tiled processing to full scene
    if aot_estimate == 'tiled':
        # print('Interpolating tiles')
        romix = tiles_interp(romix, xnew, ynew,
                             target_mask=(valid_mask if slicing else None),
                             target_mask_full=True, smooth=tile_smoothing,
                             kern_size=tile_smoothing_kernel_size,
                             method=tile_interp_method)

        astot = tiles_interp(astot, xnew, ynew,
                             target_mask=(valid_mask if slicing else None),
                             target_mask_full=True, smooth=tile_smoothing,
                             kern_size=tile_smoothing_kernel_size,
                             method=tile_interp_method)
        dutott = tiles_interp(dutott, xnew, ynew,
                              target_mask=(valid_mask if slicing else None),
                              target_mask_full=True, smooth=tile_smoothing,
                              kern_size=tile_smoothing_kernel_size,
                              method=tile_interp_method)

    ## create full scene parameters for segmented processing
    if aot_estimate == 'segmented':
        romix_ = romix * 1.0
        astot_ = astot * 1.0
        dutott_ = dutott * 1.0
        romix = np.zeros(global_attrs['data_dimensions']) + np.nan
        astot = np.zeros(global_attrs['data_dimensions']) + np.nan
        dutott = np.zeros(global_attrs['data_dimensions']) + np.nan

        for sidx, segment in enumerate(segment_data):
            romix[segment_data[segment]['sub']] = romix_[sidx]
            astot[segment_data[segment]['sub']] = astot_[sidx]
            dutott[segment_data[segment]['sub']] = dutott_[sidx]
        del romix_, astot_, dutott_

    ## write ac parameters
    # if write_tiled_parameters:
    if len(np.atleast_1d(romix) > 1):
        if romix.shape == b_data.shape:
            l2r['inputs'][f'romix_{b_dict["att"]["wave_name"]}'] = romix
        else:
            b_dict['att']['romix'] = romix[0]
    if len(np.atleast_1d(astot) > 1):
        if astot.shape == b_data.shape:
            l2r['inputs'][f'astot_{b_dict["att"]["wave_name"]}'] = astot
        else:
            b_dict['att']['astot'] = astot[0]
    if len(np.atleast_1d(dutott) > 1):
        if dutott.shape == b_data.shape:
            l2r['inputs'][f'dutott_{b_dict["att"]["wave_name"]}'] = dutott
        else:
            b_dict['att']['dutott'] = dutott[0]

    ## do atmospheric correction
    rhot_noatm = (b_data / b_dict["att"]['tt_gas']) - romix
    del romix
    b_data = (rhot_noatm) / (dutott + astot * rhot_noatm)
    del astot, dutott, rhot_noatm

    return b_data, ttot_all, valid_mask