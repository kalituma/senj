import numpy as np
from core.util import rsr_convolute_nd, tiles_interp

def exp_correction(b_dict, b_data, b_num,
                   lutdw, par, rhoam, xi, exp_lut, short_wv, long_wv, epsilon, mask, fixed_epsilon, fixed_rhoam):

    ## get Rayleigh correction
    rorayl_cur = lutdw[exp_lut]['rgi'][b_num]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
    dutotr_cur = lutdw[exp_lut]['rgi'][b_num]((xi[0], lutdw[exp_lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], 0.001))

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

def dsf_correction(b_dict, b_data, b_slot, b_num, xnew, ynew, l1r_band_list, gk_vza, gk_raa, hyper_res, user_settings, global_attrs, l2r,
                   gk, aot_sel, aot_lut, rsrd, luts, lutdw, data_mem, segment_data, use_revlut, par, is_hyper):

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

    ttot_all = {}

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

    for li, lut in enumerate(luts):
        ls = np.where(aot_lut == li)
        if len(ls[0]) == 0:
            continue
        ai = aot_sel[ls]

        ## resolved geometry with fixed path reflectance
        if use_revlut and aot_estimate == 'fixed':
            ls = np.where(b_data)

        if use_revlut:
            xi = [data_mem['pressure' + gk][ls], data_mem['raa' + gk_raa][ls], data_mem['vza' + gk_vza][ls], data_mem['sza' + gk][ls], data_mem['wind' + gk][ls]]
        else:
            xi = [data_mem['pressure' + gk], data_mem['raa' + gk_raa], data_mem['vza' + gk_vza], data_mem['sza' + gk], data_mem['wind' + gk]]
            # subset to number of estimates made for this LUT
            ## QV 2022-07-28 maybe not needed any more?
            # if len(xi[0]) > 1:
            #    xi = [[x[l] for l in ls[0]] for x in xi]

        if is_hyper:
            ## compute hyper results and resample later
            if hyper_res is None:
                hyper_res = {}
                for prm in [par, 'astot', 'dutott', 'ttot']:
                    if len(ai) == 1:  ## fixed DSF
                        hyper_res[prm] = lutdw[lut]['rgi']((xi[0], lutdw[lut]['ipd'][prm],
                                                            lutdw[lut]['meta']['wave'], xi[1], xi[2], xi[3],
                                                            xi[4], ai)).flatten()
                    else:  ## tiled/resolved DSF
                        hyper_res[prm] = np.zeros((len(lutdw[lut]['meta']['wave']), len(ai))) + np.nan
                        for iii in range(len(ai)):
                            if len(xi[0]) == 1:
                                hyper_res[prm][:, iii] = lutdw[lut]['rgi']((xi[0], lutdw[lut]['ipd'][prm],
                                                                            lutdw[lut]['meta']['wave'], xi[1],
                                                                            xi[2], xi[3], xi[4],
                                                                            ai[iii])).flatten()
                            else:
                                hyper_res[prm][:, iii] = lutdw[lut]['rgi'](
                                    (xi[0].flatten()[iii], lutdw[lut]['ipd'][prm],
                                     lutdw[lut]['meta']['wave'], xi[1].flatten()[iii], xi[2].flatten()[iii],
                                     xi[3].flatten()[iii], xi[4].flatten()[iii], ai[iii])).flatten()

            ## resample to current band
            ### path reflectance
            romix[ls] = rsr_convolute_nd(hyper_res[par], lutdw[lut]['meta']['wave'],
                                         rsrd['rsr'][b_num]['response'],
                                         rsrd['rsr'][b_num]['wave'], axis=0)
            ## transmittance and spherical albedo
            astot[ls] = rsr_convolute_nd(hyper_res['astot'], lutdw[lut]['meta']['wave'],
                                         rsrd['rsr'][b_num]['response'],
                                         rsrd['rsr'][b_num]['wave'], axis=0)
            dutott[ls] = rsr_convolute_nd(hyper_res['dutott'], lutdw[lut]['meta']['wave'],
                                          rsrd['rsr'][b_num]['response'],
                                          rsrd['rsr'][b_num]['wave'], axis=0)

            ## total transmittance
            if glint_correction and glint_correction_method == 'default':
                ttot_all[b_slot][ls] = rsr_convolute_nd(hyper_res['ttot'], lutdw[lut]['meta']['wave'],
                                                        rsrd['rsr'][b_num]['response'],
                                                        rsrd['rsr'][b_num]['wave'],
                                                        axis=0)
        else:
            ## path reflectance
            romix[ls] = lutdw[lut]['rgi'][b_num]((xi[0], lutdw[lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], ai))

            ## transmittance and spherical albedo
            astot[ls] = lutdw[lut]['rgi'][b_num]((xi[0], lutdw[lut]['ipd']['astot'], xi[1], xi[2], xi[3], xi[4], ai))
            dutott[ls] = lutdw[lut]['rgi'][b_num](
                (xi[0], lutdw[lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], ai))

            ## total transmittance
            if glint_correction and glint_correction_method == 'default':
                ttot_all[b_slot][ls] = lutdw[lut]['rgi'][b_num](
                    (xi[0], lutdw[lut]['ipd']['ttot'], xi[1], xi[2], xi[3], xi[4], ai))
        del ls, ai, xi

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