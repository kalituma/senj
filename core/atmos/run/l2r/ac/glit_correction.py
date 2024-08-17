import time
import numpy as np

import core.atmos as atmos
from core.util import tiles_interp, rsr_convolute_dict

def correct_glint_alt(l2r, aot_sel, aot_lut, var_mem, lut_mod_names, lut_table, l2r_band_list:list, rsrd, segment_data, gk:str, gk_raa:str, gk_vza:str, is_hyper:bool, user_settings:dict, global_attrs:dict):

    def _load_params():
        aot_estimate = user_settings['dsf_aot_estimate']
        residual_glint_wave_range = user_settings['dsf_residual_glint_wave_range']
        mask_rhos_threshold = user_settings['glint_mask_rhos_threshold']
        write_rhog_all = user_settings['glint_write_rhog_all']

        return aot_estimate, residual_glint_wave_range, mask_rhos_threshold, write_rhog_all

    aot_estimate, residual_glint_wave_range, mask_rhos_threshold, write_rhog_all = _load_params()

    ## reference aot and wind speed
    if aot_estimate == 'fixed':
        gc_aot = max(0.1, global_attrs['ac_aot_550'])
        gc_wind = 20
        gc_lut = global_attrs['ac_model']

        raa = global_attrs['raa']
        sza = global_attrs['sza']
        vza = global_attrs['vza']

        ## get surface reflectance for fixed geometry
        if len(np.atleast_1d(raa)) == 1:
            if is_hyper:
                surf = lut_table[gc_lut]['rgi']((global_attrs['pressure'], lut_table[gc_lut]['ipd']['rsky_s'], lut_table[gc_lut]['meta']['wave'], raa, vza, sza, gc_wind, gc_aot))
                surf_res = atmos.shared.rsr_convolute_dict(lut_table[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
            else:
                surf_res = {b: lut_table[gc_lut]['rgi'][b]((global_attrs['pressure'], lut_table[gc_lut]['ipd']['rsky_s'], raa, vza, sza, gc_wind, gc_aot)) for b in lut_table[gc_lut]['rgi']}

    if aot_estimate == 'segmented':
        for sidx, segment in enumerate(segment_data):
            gc_aot = max(0.1, aot_sel[sidx])
            gc_wind = 20
            gc_lut = lut_mod_names[aot_lut[sidx][0]]

            if sidx == 0:
                surf_res = {}
            ## get surface reflectance for segmented geometry
            # if len(np.atleast_1d(raa)) == 1:
            if is_hyper:
                surf = lut_table[gc_lut]['rgi'](
                    (
                        var_mem['pressure' + gk][sidx],
                        lut_table[gc_lut]['ipd']['rsky_s'],
                        lut_table[gc_lut]['meta']['wave'],
                        var_mem['raa' + gk_raa][sidx],
                        var_mem['vza' + gk_vza][sidx],
                        var_mem['sza' + gk][sidx],
                        gc_wind, gc_aot
                    )
                )

                surf_res[segment] = rsr_convolute_dict(lut_table[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
            else:
                surf_res[segment] = {b: lut_table[gc_lut]['rgi'][b]((var_mem['pressure' + gk][sidx],
                                                                     lut_table[gc_lut]['ipd']['rsky_s'],
                                                                     var_mem['raa' + gk_raa][sidx],
                                                                     var_mem['vza' + gk_vza][sidx],
                                                                     var_mem['sza' + gk][sidx],
                                                                     gc_wind, gc_aot)
                                                                    ) for b in lut_table[gc_lut]['rgi']}

    ## get reference surface reflectance
    gc_ref = None
    for ib, (band_slot, b_v) in enumerate(l2r["bands"].items()):
        band_num = band_slot[1:]
        rhos_ds = b_v['att']['rhos_ds']
        if rhos_ds not in l2r_band_list:
            continue
        if (b_v['att']['wavelength'] < residual_glint_wave_range[0]) or (b_v['att']['wavelength'] > residual_glint_wave_range[1]):
            continue

        # print(f'Reading reference for glint correction from band {band_slot} ({b_v["att"]["wave_name"]} nm)')

        if aot_estimate == 'fixed':
            gc_sur_cur = surf_res[band_num]
        if aot_estimate == 'segmented':
            gc_sur_cur = l2r['bands'][band_slot] * np.nan
            for segment in segment_data:
                gc_sur_cur[segment_data[segment]['sub']] = surf_res[segment][band_num]

        if gc_ref is None:
            gc_ref = b_v['data'] * 1.0
            gc_sur = gc_sur_cur
        else:
            gc_ref = np.dstack((gc_ref, b_v['data'] * 1.0))
            gc_sur = np.dstack((gc_sur, gc_sur_cur))

    if gc_ref is None:
        print(f'No bands found between {residual_glint_wave_range[0]} and {residual_glint_wave_range[1]} nm for glint correction')
    else:
        ## compute average reference glint
        if len(gc_ref.shape) == 3:
            gc_ref[gc_ref < 0] = np.nan
            gc_ref_mean = np.nanmean(gc_ref, axis=2)
            gc_ref_std = np.nanstd(gc_ref, axis=2)
            gc_ref = None

            l2r['glint_mean'] = gc_ref_mean
            l2r['glint_std'] = gc_ref_std
        else:  ## or use single band
            gc_ref[gc_ref < 0] = 0.0
            gc_ref_mean = gc_ref * 1.0

        ## compute average modeled surface glint
        axis = None
        if aot_estimate == 'segmented':
            axis = 2
        gc_sur_mean = np.nanmean(gc_sur, axis=axis)
        gc_sur_std = np.nanstd(gc_sur, axis=axis)

        ## get subset where to apply glint correction
        gc_sub = np.where(gc_ref_mean < mask_rhos_threshold)

        ## glint correction per band
        for ib, (band_slot, b_v) in enumerate(l2r['bands'].items()):
            rhos_ds = b_v['att']['rhos_ds']
            band_name = band_slot[1:]
            if rhos_ds not in l2r_band_list:
                continue
            print(f'Performing glint correction for band {band_slot} ({b_v["att"]["wave_name"]} nm)')

            ## estimate current band glint from reference glint image and ratio of interface reflectance
            if aot_estimate == 'fixed':
                sur = surf_res[band_name] * 1.0

            if aot_estimate == 'segmented':
                sur = gc_ref_mean * np.nan
                for segment in segment_data:
                    sur[segment_data[segment]['sub']] = surf_res[segment][band_name]
                sur = sur[gc_sub]

            if len(np.atleast_2d(gc_sur_mean)) == 1:
                cur_rhog = gc_ref_mean[gc_sub] * (sur / gc_sur_mean)
            else:
                cur_rhog = gc_ref_mean[gc_sub] * (sur / gc_sur_mean[gc_sub])

            ## remove glint from rhos
            cur_data = b_v['data'].copy()
            cur_data[gc_sub] -= cur_rhog
            b_v['data'] = cur_data

            ## write band glint
            if write_rhog_all:
                tmp = np.zeros(global_attrs['data_dimensions'], dtype=np.float32) + np.nan
                tmp[gc_sub] = cur_rhog
                rhog_key = f'rhog_{b_v["att"]["wave_name"]}'
                l2r[rhog_key] = {}
                l2r[rhog_key]['data'] = tmp
                l2r[rhog_key]['att'] = {'wavelength': b_v['att']['wavelength']}
                tmp = None
            cur_rhog = None

    return l2r

## end alternative glint correction

def correct_glint(l1r:dict, rsrd:dict, xnew, ynew, segment_data, ttot_all:dict, l2r:dict, l2r_band_list:list, rhos_to_band_name:list,
                  user_settings:dict, global_attrs:dict):

    def _load_params():
        mask_rhos_wave = user_settings['glint_mask_rhos_wave']
        mask_rhos_threshold = user_settings['glint_mask_rhos_threshold']
        glint_force_band = user_settings['glint_force_band']
        write_rhog_ref = user_settings['glint_write_rhog_ref']
        write_rhog_all = user_settings['glint_write_rhog_all']
        aot_estimate = user_settings['dsf_aot_estimate']
        slicing = user_settings['slicing']
        tile_smoothing = user_settings['dsf_tile_smoothing']
        tile_smoothing_kernel_size = user_settings['dsf_tile_smoothing_kernel_size']
        tile_interp_method = user_settings['dsf_tile_interp_method']
        write_tiled_parameters = user_settings['dsf_write_tiled_parameters']


        return mask_rhos_wave, mask_rhos_threshold, glint_force_band, write_rhog_ref, write_rhog_all, aot_estimate, slicing, tile_smoothing, tile_smoothing_kernel_size, tile_interp_method, write_tiled_parameters

    mask_rhos_wave, mask_rhos_threshold, glint_force_band, write_rhog_ref, write_rhog_all, aot_estimate, \
        slicing, tile_smoothing, tile_smoothing_kernel_size, tile_interp_method, write_tiled_parameters = _load_params()

    ## find bands for glint correction
    gc_swir1, gc_swir2 = None, None
    gc_swir1_b, gc_swir2_b = None, None
    swir1d, swir2d = 1000, 1000
    gc_user, gc_mask = None, None
    gc_user_b, gc_mask_b = None, None
    userd, maskd = 1000, 1000

    for band_slot, b_v in l2r['bands'].items():
        ## swir1
        sd = np.abs(b_v['att']['wave_nm'] - 1600)
        if sd < 100:
            if sd < swir1d:
                gc_swir1 = b_v['att']['rhos_ds']
                swir1d = sd
                gc_swir1_b = band_slot
        ## swir2
        sd = np.abs(b_v['att']['wave_nm'] - 2200)
        if sd < 100:
            if sd < swir2d:
                gc_swir2 = b_v['att']['rhos_ds']
                swir2d = sd
                gc_swir2_b = band_slot
        ## mask band
        sd = np.abs(b_v['att']['wave_nm'] - mask_rhos_wave)
        if sd < 100:
            if sd < maskd:
                gc_mask = b_v['att']['rhos_ds']
                maskd = sd
                gc_mask_b = band_slot
        ## user band
        if glint_force_band is not None:
            sd = np.abs(b_v['att']['wave_nm'] - glint_force_band)
            if sd < 100:
                if sd < userd:
                    gc_user = b_v['att']['rhos_ds']
                    userd = sd
                    gc_user_b = band_slot

    ## use user selected  band
    if gc_user is not None:
        gc_swir1, gc_swir1_b = None, None
        gc_swir2, gc_swir2_b = None, None

    ## start glint correction
    if (gc_swir1 is not None and gc_swir2 is not None) or (gc_user is not None):
        t0 = time.time()
        # print('Starting glint correction')

        ## compute scattering angle
        dtor = np.pi / 180.
        sza = l1r['sza'] * dtor
        vza = l1r['vza'] * dtor
        raa = l1r['raa'] * dtor

        ## flatten 1 element arrays
        if sza.shape == (1, 1):
            sza = sza.flatten()
        if vza.shape == (1, 1):
            vza = vza.flatten()
        if raa.shape == (1, 1):
            raa = raa.flatten()

        muv = np.cos(vza)
        mus = np.cos(sza)
        cos2omega = mus * muv + np.sin(sza) * np.sin(vza) * np.cos(raa)
        del sza, vza, raa

        omega = np.arccos(cos2omega) / 2
        del cos2omega

        ## read and resample refractive index
        refri = atmos.ac.refri()
        refri_sen = rsr_convolute_dict(refri['wave'] / 1000, refri['n'], rsrd['rsr'])

        ## compute fresnel reflectance for the reference bands
        Rf_sen = {}
        for b in [gc_swir1_b, gc_swir2_b, gc_user_b]:
            if b is None:
                continue
            band_name = b[1:]
            Rf_sen[b] = atmos.ac.sky_refl(omega, n_w=refri_sen[band_name])

        ## compute where to apply the glint correction
        ## sub_gc has the idx for non masked data with rhos_ref below the masking threshold
        gc_mask_data = l2r['bands'][gc_mask_b]['data']

        if gc_mask_data is None:  ## reference rhos dataset can be missing for night time images (tgas computation goes negative)
            print('No glint mask could be determined.')
        else:
            sub_gc = np.where(np.isfinite(gc_mask_data) & (gc_mask_data <= mask_rhos_threshold))
            del gc_mask_data

            ## get reference bands transmittance
            for ib, (band_slot, b_v) in enumerate(l2r['bands'].items()):
                rhos_ds = b_v['att']['rhos_ds']
                if rhos_ds not in [gc_swir1, gc_swir2, gc_user]:
                    continue
                if rhos_ds not in l2r_band_list:
                    continue

                ## two way direct transmittance
                if aot_estimate == 'tiled':
                    if slicing:
                        ## load rhos dataset
                        cur_data = l2r['bands'][band_slot]['data'].copy()
                        valid_mask = np.isfinite(cur_data)
                        del cur_data
                    ttot_all_b = tiles_interp(ttot_all[band_slot], xnew, ynew,
                                                           target_mask=(valid_mask if slicing else None),
                                                           target_mask_full=True,
                                                           smooth=tile_smoothing,
                                                           kern_size=tile_smoothing_kernel_size,
                                                           method=tile_interp_method)

                elif aot_estimate == 'segmented':
                    ttot_all_ = ttot_all[b] * 1.0
                    ttot_all_b = np.zeros(global_attrs['data_dimensions']) + np.nan
                    for sidx, segment in enumerate(segment_data):
                        ttot_all_b[segment_data[segment]['sub']] = ttot_all_[sidx]
                    del ttot_all_
                else:
                    ttot_all_b = ttot_all[b] * 1.0

                T_cur = np.exp(-1. * (ttot_all_b / muv)) * np.exp(-1. * (ttot_all_b / mus))
                del ttot_all_b

                ## subset if 2d
                T_cur_sub = T_cur[sub_gc] if len(np.atleast_2d(T_cur)) > 1 else T_cur[0] * 1.0

                if rhos_ds == gc_user:
                    T_USER = T_cur_sub * 1.0
                else:
                    if rhos_ds == gc_swir1:
                        T_SWIR1 = T_cur_sub * 1.0
                    if rhos_ds == gc_swir2:
                        T_SWIR2 = T_cur_sub * 1.0
                del T_cur, T_cur_sub

            ## swir band choice is made for first band
            gc_choice = False
            ## glint correction per band
            for ib, (band_slot, b_v) in enumerate(l2r['bands'].items()):
                rhos_ds = b_v['att']['rhos_ds']
                if rhos_ds not in l2r_band_list:
                    continue
                if band_slot not in ttot_all:
                    continue
                # print(f'Performing glint correction for band {band_slot} ({b_v["att"]["wave_name"]} nm)')
                ## load rhos dataset
                cur_data = l2r['bands'][band_slot]['data'].copy()

                ## two way direct transmittance
                if aot_estimate == 'tiled':
                    if slicing:
                        valid_mask = np.isfinite(cur_data)
                    ttot_all_b = tiles_interp(ttot_all[band_slot], xnew, ynew,
                                              target_mask=(valid_mask if slicing else None),
                                              target_mask_full=True,
                                              smooth=tile_smoothing,
                                              kern_size=tile_smoothing_kernel_size,
                                              method=tile_interp_method)
                elif aot_estimate == 'segmented':
                    ttot_all_ = ttot_all[band_slot] * 1.0
                    ttot_all_b = np.zeros(global_attrs['data_dimensions']) + np.nan
                    for sidx, segment in enumerate(segment_data):
                        ttot_all_b[segment_data[segment]['sub']] = ttot_all_[sidx]
                    del ttot_all_
                else:
                    ttot_all_b = ttot_all[band_slot] * 1.0
                if write_tiled_parameters:
                    if len(np.atleast_1d(ttot_all_b) > 1):
                        ttot_key = f'ttot_{b_v["att"]["wave_name"]}'
                        if ttot_all_b.shape == muv.shape:
                            l2r['inputs'][ttot_key] = ttot_all_b
                        else:
                            l2r['inputs'][ttot_key] = ttot_all_b[0]
                ## end compute ttot_all_band

                T_cur = np.exp(-1. * (ttot_all_b / muv)) * np.exp(-1. * (ttot_all_b / mus))
                del ttot_all_b

                ## subset if 2d
                T_cur_sub = T_cur[sub_gc] if len(np.atleast_2d(T_cur)) > 1 else T_cur[0] * 1.0
                del T_cur

                ## get current band Fresnel reflectance
                Rf_sen_cur = atmos.ac.sky_refl(omega, n_w=refri_sen[band_slot[1:]])

                ## get gc factors for this band
                if gc_user is None:
                    if len(np.atleast_2d(Rf_sen[gc_swir1_b])) > 1:  ## if resolved angles
                        gc_SWIR1 = (T_cur_sub / T_SWIR1) * (Rf_sen_cur[sub_gc] / Rf_sen[gc_swir1_b][sub_gc])
                        gc_SWIR2 = (T_cur_sub / T_SWIR2) * (Rf_sen_cur[sub_gc] / Rf_sen[gc_swir2_b][sub_gc])
                    else:
                        gc_SWIR1 = (T_cur_sub / T_SWIR1) * (Rf_sen_cur / Rf_sen[gc_swir1_b])
                        gc_SWIR2 = (T_cur_sub / T_SWIR2) * (Rf_sen_cur / Rf_sen[gc_swir2_b])
                else:
                    if len(np.atleast_2d(Rf_sen[gc_user_b])) > 1:  ## if resolved angles
                        gc_USER = (T_cur_sub / T_USER) * (Rf_sen_cur[sub_gc] / Rf_sen[gc_user_b][sub_gc])
                    else:
                        gc_USER = (T_cur_sub / T_USER) * (Rf_sen_cur / Rf_sen[gc_user_b])
                del Rf_sen_cur, T_cur_sub

                ## choose glint correction band (based on first band results)
                if gc_choice is False:
                    gc_choice = True
                    if gc_user is None:
                        swir1_rhos = l2r['bands'][rhos_to_band_name[gc_swir1]]['data'][sub_gc].copy()
                        swir2_rhos = l2r['bands'][rhos_to_band_name[gc_swir2]]['data'][sub_gc].copy()
                        ## set negatives to 0
                        swir1_rhos[swir1_rhos < 0] = 0
                        swir2_rhos[swir2_rhos < 0] = 0
                        ## estimate glint correction in the blue band
                        g1_blue = gc_SWIR1 * swir1_rhos
                        g2_blue = gc_SWIR2 * swir2_rhos
                        ## use SWIR1 or SWIR2 based glint correction
                        use_swir1 = np.where(g1_blue < g2_blue)
                        del g1_blue, g2_blue
                        rhog_ref = swir2_rhos
                        rhog_ref[use_swir1] = swir1_rhos[use_swir1]
                        del swir1_rhos, swir2_rhos
                    else:
                        rhog_ref = l2r['bands'][rhos_to_band_name[gc_user]]['data'].copy()
                        ## set negatives to 0
                        rhog_ref[rhog_ref < 0] = 0
                    ## write reference glint
                    if write_rhog_ref:
                        tmp = np.zeros(global_attrs['data_dimensions'], dtype=np.float32) + np.nan
                        tmp[sub_gc] = rhog_ref
                        l2r['rhog_ref'] = tmp
                ## end select glint correction band

                ## calculate glint in this band
                if gc_user is None:
                    cur_rhog = gc_SWIR2 * rhog_ref
                    try:
                        cur_rhog[use_swir1] = gc_SWIR1[use_swir1] * rhog_ref[use_swir1]
                    except:
                        cur_rhog[use_swir1] = gc_SWIR1 * rhog_ref[use_swir1]
                    del gc_SWIR1, gc_SWIR2
                else:
                    cur_rhog = gc_USER * rhog_ref
                    del gc_USER

                ## remove glint from rhos
                cur_data[sub_gc] -= cur_rhog
                l2r['bands'][rhos_to_band_name[rhos_ds]]['data'] = cur_data
                del cur_data

                ## write band glint
                if write_rhog_all:
                    tmp = np.zeros(global_attrs['data_dimensions'], dtype=np.float32) + np.nan
                    tmp[sub_gc] = cur_rhog
                    l2r[f'rhog_{b_v["att"]["wave_name"]}'] = {}
                    l2r[f'rhog_{b_v["att"]["wave_name"]}']['data'] = tmp
                    l2r[f'rhog_{b_v["att"]["wave_name"]}']['att'] = {'wavelength': b_v['att']['wavelength']}
                    del tmp
                del cur_rhog
            del sub_gc, rhog_ref
            if gc_user is not None:
                del T_USER
            else:
                del T_SWIR1, T_SWIR2, use_swir1
        del Rf_sen, omega, muv, mus
    if (aot_estimate == 'tiled') and slicing:
        del valid_mask

    return l2r