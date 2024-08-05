import time
import numpy as np

from core.util import rsr_convolute_nd

def calc_surface_reflectance(band_ds, data_mem, l1r_band_list, rho_cirrus, user_settings:dict):
    hyper_res = None
    ## compute surface reflectances
    for bi, (band_slot, b_v) in enumerate(band_ds.items()):
        band_num = band_slot[1:]
        if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm not in bands dataset')
            continue
        if b_v['att']['rhot_ds'] not in l1r_band_list:
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm not in available rhot datasets')
            continue  ## skip if we don't have rhot for a band that is in the RSR file

        ## temporary fix
        if b_v['att']['wave_mu'] < 0.345:
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm wavelength < 345 nm')
            continue  ## skip if below LUT range

        rhot_name = b_v['att']['rhot_ds']  # dsi
        rhos_name = b_v['att']['rhos_ds']  # dso
        cur_data, cur_att = b_v['data'].copy(), b_v['att'].copy()

        ## store rhot in output file

        if b_v['att']['tt_gas'] < user_settings['min_tgas_rho']:
            print(
                f'Band {band_slot} at {b_v["att"]["wave_name"]} nm has tgas < min_tgas_rho ({b_v["att"]["tt_gas"]:.2f} < {user_settings["min_tgas_rho"]:.2f})')
            continue

        ## apply cirrus correction
        if user_settings['cirrus_correction']:
            g = user_settings['cirrus_g_vnir'] * 1.0
            if b_v['att']['wave_nm'] > 1000:
                g = user_settings['cirrus_g_swir'] * 1.0
            cur_data -= (rho_cirrus * g)

        t0 = time.time()
        print('Computing surface reflectance', band_slot, b_v['att']['wave_name'], f'{b_v["att"]["tt_gas"]:.3f}')

        ds_att = b_v['att']
        ds_att['wavelength'] = ds_att['wave_nm']

        ## dark spectrum fitting
        if (ac_opt == 'dsf'):
            if user_settings['slicing']:
                valid_mask = np.isfinite(cur_data)

            ## shape of atmospheric datasets
            atm_shape = aot_sel.shape

            ## if path reflectance is resolved, but resolved geometry available
            if (use_revlut) & (user_settings['dsf_aot_estimate'] == 'fixed'):
                atm_shape = cur_data.shape
                gk = ''

            ## use band specific geometry if available
            gk_raa = f'{gk}'
            gk_vza = f'{gk}'
            if f'raa_{b_v["att"]["wave_name"]}' in l1r_datasets:
                gk_raa = f'_{b_v["att"]["wave_name"]}' + gk_raa
            if 'vza_{}'.format(b_v["att"]["wave_name"]) in l1r_datasets:
                gk_vza = f'_{b_v["att"]["wave_name"]}' + gk_vza

            romix = np.zeros(atm_shape, dtype=np.float32) + np.nan
            astot = np.zeros(atm_shape, dtype=np.float32) + np.nan
            dutott = np.zeros(atm_shape, dtype=np.float32) + np.nan

            if (user_settings['dsf_residual_glint_correction']) & (
                    user_settings['dsf_residual_glint_correction_method'] == 'default'):
                ttot_all[band_slot] = np.zeros(atm_shape, dtype=np.float32) + np.nan

            for li, lut in enumerate(luts):
                ls = np.where(aot_lut == li)
                if len(ls[0]) == 0:
                    continue
                ai = aot_sel[ls]

                ## resolved geometry with fixed path reflectance
                if (use_revlut) & (user_settings['dsf_aot_estimate'] == 'fixed'):
                    ls = np.where(cur_data)

                if (use_revlut):
                    xi = [data_mem['pressure' + gk][ls],
                          data_mem['raa' + gk_raa][ls],
                          data_mem['vza' + gk_vza][ls],
                          data_mem['sza' + gk][ls],
                          data_mem['wind' + gk][ls]]
                else:
                    xi = [data_mem['pressure' + gk],
                          data_mem['raa' + gk_raa],
                          data_mem['vza' + gk_vza],
                          data_mem['sza' + gk],
                          data_mem['wind' + gk]]
                    # subset to number of estimates made for this LUT
                    ## QV 2022-07-28 maybe not needed any more?
                    # if len(xi[0]) > 1:
                    #    xi = [[x[l] for l in ls[0]] for x in xi]

                if hyper:
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
                                                              rsrd['rsr'][band_num]['response'],
                                                              rsrd['rsr'][band_num]['wave'], axis=0)
                    ## transmittance and spherical albedo
                    astot[ls] = rsr_convolute_nd(hyper_res['astot'], lutdw[lut]['meta']['wave'],
                                                              rsrd['rsr'][band_num]['response'],
                                                              rsrd['rsr'][band_num]['wave'], axis=0)
                    dutott[ls] = rsr_convolute_nd(hyper_res['dutott'], lutdw[lut]['meta']['wave'],
                                                               rsrd['rsr'][band_num]['response'],
                                                               rsrd['rsr'][band_num]['wave'], axis=0)

                    ## total transmittance
                    if (user_settings['dsf_residual_glint_correction']) & (
                            user_settings['dsf_residual_glint_correction_method'] == 'default'):
                        ttot_all[band_slot][ls] = rsr_convolute_nd(hyper_res['ttot'],
                                                                                lutdw[lut]['meta']['wave'],
                                                                                rsrd['rsr'][band_num]['response'],
                                                                                rsrd['rsr'][band_num]['wave'],
                                                                                axis=0)
                else:
                    ## path reflectance
                    romix[ls] = lutdw[lut]['rgi'][band_num](
                        (xi[0], lutdw[lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], ai))

                    ## transmittance and spherical albedo
                    astot[ls] = lutdw[lut]['rgi'][band_num](
                        (xi[0], lutdw[lut]['ipd']['astot'], xi[1], xi[2], xi[3], xi[4], ai))
                    dutott[ls] = lutdw[lut]['rgi'][band_num](
                        (xi[0], lutdw[lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], ai))

                    ## total transmittance
                    if (user_settings['dsf_residual_glint_correction']) & (
                            user_settings['dsf_residual_glint_correction_method'] == 'default'):
                        ttot_all[band_slot][ls] = lutdw[lut]['rgi'][band_num](
                            (xi[0], lutdw[lut]['ipd']['ttot'], xi[1], xi[2], xi[3], xi[4], ai))
                del ls, ai, xi

            ## interpolate tiled processing to full scene
            if user_settings['dsf_aot_estimate'] == 'tiled':
                print('Interpolating tiles')
                romix = atmos.shared.tiles_interp(romix, xnew, ynew,
                                                  target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                  target_mask_full=True, smooth=user_settings['dsf_tile_smoothing'],
                                                  kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                  method=user_settings['dsf_tile_interp_method'])
                astot = atmos.shared.tiles_interp(astot, xnew, ynew,
                                                  target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                  target_mask_full=True, smooth=user_settings['dsf_tile_smoothing'],
                                                  kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                  method=user_settings['dsf_tile_interp_method'])
                dutott = atmos.shared.tiles_interp(dutott, xnew, ynew,
                                                   target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                   target_mask_full=True, smooth=user_settings['dsf_tile_smoothing'],
                                                   kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                   method=user_settings['dsf_tile_interp_method'])

            ## create full scene parameters for segmented processing
            if user_settings['dsf_aot_estimate'] == 'segmented':
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
            if user_settings['dsf_write_tiled_parameters']:
                if len(np.atleast_1d(romix) > 1):
                    if romix.shape == cur_data.shape:
                        l2r['inputs'][f'romix_{b_v["att"]["wave_name"]}'] = romix
                    else:
                        ds_att['romix'] = romix[0]
                if len(np.atleast_1d(astot) > 1):
                    if astot.shape == cur_data.shape:
                        l2r['inputs'][f'astot_{b_v["att"]["wave_name"]}'] = astot
                    else:
                        ds_att['astot'] = astot[0]
                if len(np.atleast_1d(dutott) > 1):
                    if dutott.shape == cur_data.shape:
                        l2r['inputs'][f'dutott_{b_v["att"]["wave_name"]}'] = dutott
                    else:
                        ds_att['dutott'] = dutott[0]

            ## do atmospheric correction
            rhot_noatm = (cur_data / b_v["att"]['tt_gas']) - romix
            del romix
            cur_data = (rhot_noatm) / (dutott + astot * rhot_noatm)
            del astot, dutott, rhot_noatm

        ## exponential
        elif (ac_opt == 'exp'):
            ## get Rayleigh correction
            rorayl_cur = lutdw[exp_lut]['rgi'][band_num](
                (xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
            dutotr_cur = lutdw[exp_lut]['rgi'][band_num](
                (xi[0], lutdw[exp_lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], 0.001))

            ## get epsilon in current band
            delta = (long_wv - b_v['att']['wave_nm']) / (long_wv - short_wv)
            eps_cur = np.power(epsilon, delta)
            rhoam_cur = rhoam * eps_cur

            ## add results to band
            if exp_fixed_epsilon:
                ds_att['epsilon'] = eps_cur
            if exp_fixed_rhoam:
                ds_att['rhoam'] = rhoam_cur

            cur_data = (cur_data - rorayl_cur - rhoam_cur) / (dutotr_cur)
            cur_data[mask] = np.nan
        ## end exponential

        ## write rhorc
        if (user_settings['output_rhorc']):
            ## read TOA
            cur_rhorc, cur_att = b_v['data'].copy(), b_v['att'].copy()

            ## compute Rayleigh parameters for DSF
            if (ac_opt == 'dsf'):
                ## no subset
                xi = [data_mem['pressure' + gk],
                      data_mem['raa' + gk_raa],
                      data_mem['vza' + gk_vza],
                      data_mem['sza' + gk],
                      data_mem['wind' + gk]]

                ## get Rayleigh parameters
                if hyper:
                    rorayl_hyper = lutdw[luts[0]]['rgi']((xi[0], lutdw[luts[0]]['ipd'][par],
                                                          lutdw[luts[0]]['meta']['wave'], xi[1], xi[2], xi[3], xi[4],
                                                          0.001)).flatten()
                    dutotr_hyper = lutdw[luts[0]]['rgi']((xi[0], lutdw[luts[0]]['ipd']['dutott'],
                                                          lutdw[luts[0]]['meta']['wave'], xi[1], xi[2], xi[3], xi[4],
                                                          0.001)).flatten()
                    rorayl_cur = atmos.shared.rsr_convolute_nd(rorayl_hyper, lutdw[luts[0]]['meta']['wave'],
                                                               rsrd['rsr'][band_num]['response'],
                                                               rsrd['rsr'][band_num]['wave'], axis=0)
                    dutotr_cur = atmos.shared.rsr_convolute_nd(dutotr_hyper, lutdw[luts[0]]['meta']['wave'],
                                                               rsrd['rsr'][band_num]['response'],
                                                               rsrd['rsr'][band_num]['wave'], axis=0)
                    del rorayl_hyper, dutotr_hyper
                else:
                    rorayl_cur = lutdw[luts[0]]['rgi'][band_num](
                        (xi[0], lutdw[luts[0]]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
                    dutotr_cur = lutdw[luts[0]]['rgi'][band_num](
                        (xi[0], lutdw[luts[0]]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], 0.001))

                del xi

            ## create full scene parameters for segmented processing
            if user_settings['dsf_aot_estimate'] == 'segmented':
                rorayl_ = rorayl_cur * 1.0
                dutotr_ = dutotr_cur * 1.0
                rorayl_cur = np.zeros(global_attrs['data_dimensions']) + np.nan
                dutotr_cur = np.zeros(global_attrs['data_dimensions']) + np.nan
                for sidx, segment in enumerate(segment_data):
                    rorayl_cur[segment_data[segment]['sub']] = rorayl_[sidx]
                    dutotr_cur[segment_data[segment]['sub']] = dutotr_[sidx]
                del rorayl_, dutotr_

            ## create full scene parameters for tiled processing
            if (user_settings['dsf_aot_estimate'] == 'tiled') & (use_revlut):
                print('Interpolating tiles for rhorc')
                rorayl_cur = atmos.shared.tiles_interp(rorayl_cur, xnew, ynew,
                                                       target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                       target_mask_full=True,
                                                       smooth=user_settings['dsf_tile_smoothing'],
                                                       kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                       method=user_settings['dsf_tile_interp_method'])
                dutotr_cur = atmos.shared.tiles_interp(dutotr_cur, xnew, ynew,
                                                       target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                       target_mask_full=True,
                                                       smooth=user_settings['dsf_tile_smoothing'],
                                                       kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                       method=user_settings['dsf_tile_interp_method'])

            ## write ac parameters
            if user_settings['dsf_write_tiled_parameters']:
                if len(np.atleast_1d(rorayl_cur) > 1):
                    if rorayl_cur.shape == cur_data.shape:
                        d_k = f'rorayl_{b_v["att"]["wave_name"]}'
                        l2r[d_k] = rorayl_cur
                        l2r_datasets.append(d_k)
                    else:
                        ds_att['rorayl'] = rorayl_cur[0]

                if len(np.atleast_1d(dutotr_cur) > 1):
                    if dutotr_cur.shape == cur_data.shape:
                        d_k = f'dutotr_{b_v["att"]["wave_name"]}'
                        l2r[d_k] = dutotr_cur
                        l2r_datasets.append(d_k)
                    else:
                        ds_att['dutotr'] = dutotr_cur[0]

            cur_rhorc = (cur_rhorc - rorayl_cur) / (dutotr_cur)

            rhoc_key = rhos_name.replace('rhos_', 'rhorc_')
            l2r[rhoc_key] = {}
            l2r[rhoc_key]['data'] = cur_rhorc
            l2r[rhoc_key]['att'] = ds_att
            l2r_datasets.append(rhoc_key)

            del cur_rhorc, rorayl_cur, dutotr_cur

        if ac_opt == 'dsf' and user_settings['slicing']:
            del valid_mask

        ## write rhos
        l2r['bands'][band_slot] = {'data': cur_data, 'att': ds_att}
        rhos_to_band_name[b_v['att']['rhos_ds']] = band_slot
        l2r_datasets.append(rhos_name)

        del cur_data
        print(
            f'{global_attrs["sensor"]}/{band_slot} took {(time.time() - t0):.1f}s ({"RevLUT" if use_revlut else "StdLUT"})')