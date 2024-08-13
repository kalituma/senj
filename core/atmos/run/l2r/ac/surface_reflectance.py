import time
import numpy as np

from core.util import rsr_convolute_nd, tiles_interp


def calc_surface_reflectance(xnew, ynew, band_table, var_mem, l1r_band_list,
                             gk, lut_table, rho_cirrus, ro_type, use_revlut, segment_data, is_hyper, ac_opt:str, luts, rsrd,  # common
                             global_attrs, user_settings:dict,  # params
                             l2r, l2r_band_list, rhos_to_band_name, corr_func  # out
                             ):

    def _load_params():
        cirrus_correction = user_settings['cirrus_correction']
        cirrus_g_vnir = user_settings['cirrus_g_vnir']
        cirrus_g_swir = user_settings['cirrus_g_swir']
        min_tgas_rho = user_settings['min_tgas_rho']
        slicing = user_settings['slicing']
        aot_estimate = user_settings['dsf_aot_estimate']
        residual_glint_correction = user_settings['dsf_residual_glint_correction']
        residual_glint_correction_method = user_settings['dsf_residual_glint_correction_method']
        tile_smoothing = user_settings['dsf_tile_smoothing']
        tile_smoothing_kernel_size = user_settings['dsf_tile_smoothing_kernel_size']
        tile_interp_method = user_settings['dsf_tile_interp_method']
        # write_tiled_parameters = user_settings['dsf_write_tiled_parameters']
        gas_transmittance = user_settings['gas_transmittance']
        add_band_name = user_settings['add_band_name']
        add_detector_name = user_settings['add_detector_name']
        output_rhorc = user_settings['output_rhorc']

        return cirrus_correction, cirrus_g_vnir, cirrus_g_swir, min_tgas_rho, slicing, aot_estimate, residual_glint_correction, \
            residual_glint_correction_method, tile_smoothing, tile_smoothing_kernel_size, tile_interp_method, gas_transmittance, add_band_name, add_detector_name, output_rhorc

    cirrus_correction, cirrus_g_vnir, cirrus_g_swir, min_tgas_rho, slicing, aot_estimate, glint_correction, \
        glint_correction_method, tile_smoothing, tile_smoothing_kernel_size, tile_interp_method, \
        gas_transmittance, add_band_name, add_detector_name, output_rhorc = _load_params()

    hyper_res = None

    if use_revlut and aot_estimate == 'fixed':
        gk = ''

    ## use band specific geometry if available
    gk_raa = f'{gk}'
    gk_vza = f'{gk}'

    ## compute surface reflectances
    for bi, (b_slot, b_dict) in enumerate(band_table.items()):
        b_num = b_slot[1:]
        if ('rhot_ds' not in b_dict['att']) or ('tt_gas' not in b_dict['att']):
            # print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm not in bands dataset')
            continue
        if b_dict['att']['rhot_ds'] not in l1r_band_list:
            # print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm not in available rhot datasets')
            continue  ## skip if we don't have rhot for a band that is in the RSR file

        ## temporary fix
        if b_dict['att']['wave_mu'] < 0.345:
            print(f'Band {b_slot} at {b_dict["att"]["wave_name"]} nm wavelength < 345 nm')
            continue  ## skip if below LUT range

        # rhot_name = b_dict['att']['rhot_ds']  # dsi
        rhos_name = b_dict['att']['rhos_ds']  # dso
        b_data, b_att = b_dict['data'].copy(), b_dict['att'].copy()

        ## store rhot in output file

        if b_dict['att']['tt_gas'] < min_tgas_rho:
            # print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm has tgas < min_tgas_rho ({b_v["att"]["tt_gas"]:.2f} < {user_settings["min_tgas_rho"]:.2f})')
            continue

        ## apply cirrus correction
        if cirrus_correction:
            g = cirrus_g_vnir * 1.0
            if b_dict['att']['wave_nm'] > 1000:
                g = cirrus_g_swir * 1.0
            b_data -= (rho_cirrus * g)

        t0 = time.time()
        # print('Computing surface reflectance', band_slot, b_v['att']['wave_name'], f'{b_v["att"]["tt_gas"]:.3f}')

        # ds_att = b_v['att']
        b_dict['att']['wavelength'] = b_dict['att']['wave_nm']

        ## dark spectrum fitting
        if ac_opt == 'dsf':
            b_data, ttot_all, valid_mask = corr_func(b_dict=b_dict, b_data=b_data, b_slot=b_slot, b_num=b_num, xnew=xnew, ynew=ynew,
                                                     l1r_band_list=l1r_band_list, gk_vza=gk_vza, gk_raa=gk_raa, hyper_res=hyper_res,
                                                     user_settings=user_settings, global_attrs=global_attrs, l2r=l2r)
        ## exponential
        elif ac_opt == 'exp':
            b_data, rorayl_cur, dutotr_cur = corr_func(b_dict=b_dict, b_data=b_data, b_num=b_num)

        ## write rhorc
        if output_rhorc:
            ## read TOA
            cur_rhorc, b_att = b_dict['data'].copy(), b_dict['att'].copy()

            ## compute Rayleigh parameters for DSF
            if ac_opt == 'dsf':
                ## no subset
                dsf_xi = [var_mem['pressure' + gk], var_mem['raa' + gk_raa], var_mem['vza' + gk_vza], var_mem['sza' + gk], var_mem['wind' + gk]]

                ## get Rayleigh parameters
                if is_hyper:
                    rorayl_hyper = lut_table[luts[0]]['rgi']((dsf_xi[0], lut_table[luts[0]]['ipd'][ro_type], lut_table[luts[0]]['meta']['wave'], dsf_xi[1], dsf_xi[2], dsf_xi[3], dsf_xi[4], 0.001)).flatten()
                    dutotr_hyper = lut_table[luts[0]]['rgi']((dsf_xi[0], lut_table[luts[0]]['ipd']['dutott'], lut_table[luts[0]]['meta']['wave'], dsf_xi[1], dsf_xi[2], dsf_xi[3], dsf_xi[4], 0.001)).flatten()

                    rorayl_cur = rsr_convolute_nd(rorayl_hyper, lut_table[luts[0]]['meta']['wave'], rsrd['rsr'][b_num]['response'], rsrd['rsr'][b_num]['wave'], axis=0)
                    dutotr_cur = rsr_convolute_nd(dutotr_hyper, lut_table[luts[0]]['meta']['wave'], rsrd['rsr'][b_num]['response'], rsrd['rsr'][b_num]['wave'], axis=0)

                    del rorayl_hyper, dutotr_hyper
                else:
                    rorayl_cur = lut_table[luts[0]]['rgi'][b_num]((dsf_xi[0], lut_table[luts[0]]['ipd'][ro_type], dsf_xi[1], dsf_xi[2], dsf_xi[3], dsf_xi[4], 0.001))
                    dutotr_cur = lut_table[luts[0]]['rgi'][b_num]((dsf_xi[0], lut_table[luts[0]]['ipd']['dutott'], dsf_xi[1], dsf_xi[2], dsf_xi[3], dsf_xi[4], 0.001))

                del dsf_xi

            ## create full scene parameters for segmented processing
            if aot_estimate == 'segmented':
                rorayl_ = rorayl_cur * 1.0
                dutotr_ = dutotr_cur * 1.0
                rorayl_cur = np.zeros(global_attrs['data_dimensions']) + np.nan
                dutotr_cur = np.zeros(global_attrs['data_dimensions']) + np.nan
                for sidx, segment in enumerate(segment_data):
                    rorayl_cur[segment_data[segment]['sub']] = rorayl_[sidx]
                    dutotr_cur[segment_data[segment]['sub']] = dutotr_[sidx]
                del rorayl_, dutotr_

            ## create full scene parameters for tiled processing
            if aot_estimate == 'tiled' and use_revlut:
                # print('Interpolating tiles for rhorc')
                rorayl_cur = tiles_interp(rorayl_cur, xnew, ynew,
                                                       target_mask=(valid_mask if slicing else None),
                                                       target_mask_full=True,
                                                       smooth=tile_smoothing,
                                                       kern_size=tile_smoothing_kernel_size,
                                                       method=tile_interp_method)
                dutotr_cur = tiles_interp(dutotr_cur, xnew, ynew,
                                                       target_mask=(valid_mask if slicing else None), \
                                                       target_mask_full=True,
                                                       smooth=tile_smoothing,
                                                       kern_size=tile_smoothing_kernel_size,
                                                       method=tile_interp_method)

            ## write ac parameters
            # if write_tiled_parameters:
            if len(np.atleast_1d(rorayl_cur) > 1):
                if rorayl_cur.shape == b_data.shape:
                    d_k = f'rorayl_{b_dict["att"]["wave_name"]}'
                    l2r[d_k] = rorayl_cur
                    l2r_band_list.append(d_k)
                else:
                    b_dict['att']['rorayl'] = rorayl_cur[0]

            if len(np.atleast_1d(dutotr_cur) > 1):
                if dutotr_cur.shape == b_data.shape:
                    d_k = f'dutotr_{b_dict["att"]["wave_name"]}'
                    l2r[d_k] = dutotr_cur
                    l2r_band_list.append(d_k)
                else:
                    b_dict['att']['dutotr'] = dutotr_cur[0]

            cur_rhorc = (cur_rhorc - rorayl_cur) / (dutotr_cur)

            rhoc_key = rhos_name.replace('rhos_', 'rhorc_')
            l2r[rhoc_key] = {}
            l2r[rhoc_key]['data'] = cur_rhorc
            l2r[rhoc_key]['att'] = b_dict['att']
            l2r_band_list.append(rhoc_key)

            del cur_rhorc, rorayl_cur, dutotr_cur

        if ac_opt == 'dsf' and slicing:
            del valid_mask

        ## write rhos
        l2r['bands'][b_slot] = {'data': b_data, 'att': b_dict['att']}
        rhos_to_band_name[b_dict['att']['rhos_ds']] = b_slot
        l2r_band_list.append(rhos_name)

        del b_data
        # print(f'{global_attrs["sensor"]}/{band_slot} took {(time.time() - t0):.1f}s ({"RevLUT" if use_revlut else "StdLUT"})')