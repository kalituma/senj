from functools import partial
import os, time, datetime
import numpy as np
import scipy.ndimage, scipy.interpolate
import skimage.measure

from core import atmos
from core.util import tiles_interp
from core.atmos.setting import parse

from core.atmos.run.l2r import check_blackfill_skip, load_rsrd, load_ancillary_data, \
    get_dem_pressure, select_lut_type, clip_angles, clip_angles_mean, prepare_attr_band_ds, build_l1r_mem
from core.atmos.run.l2r.ac import apply_dsf, apply_ac_exp, correct_cirrus, calc_surface_reflectance, dsf_correction, exp_correction

def apply_l2r(l1r:dict, global_attrs:dict):

    var_mem = {}
    l2r = {}
    l2r_band_list = []
    rhos_to_band_name = {}
    # l2r['bands'] = {}
    # l2r['inputs'] = {}
    #

    user_settings = parse(global_attrs['sensor'], settings=atmos.settings['user'])

    for k in user_settings:
        atmos.settings['run'][k] = user_settings[k]

    if user_settings['dsf_exclude_bands'] != None:
        if type(user_settings['dsf_exclude_bands']) != list:
            user_settings['dsf_exclude_bands'] = [user_settings['dsf_exclude_bands']]
    else:
        user_settings['dsf_exclude_bands'] = []

    band_table = l1r['bands'].copy()

    rhot_names = [band_table[key]['att']['rhot_ds'] for key in band_table]
    rhot_bands = {
        rhot_name: band_table[key]['data'] for key, rhot_name in zip(band_table.keys(), rhot_names)
    }
    l1r_band_list = list(l1r.keys())[:-1] + rhot_names

    if user_settings['blackfill_skip']:
        if check_blackfill_skip(band_table, user_settings):
            return ()

    # print(f'Running acolite for {setu["inputfile"]}')

    last_band_key = list(band_table.keys())[-1]
    global_attrs['data_dimensions'] = band_table[last_band_key]['data'].shape
    global_attrs['data_elements'] = global_attrs['data_dimensions'][0] * global_attrs['data_dimensions'][1]

    rsrd, is_hyper = load_rsrd(global_attrs)

    if global_attrs['sensor'] in rsrd:
        rsrd = rsrd[global_attrs['sensor']]
    else:
        print(f'Could not find {global_attrs["sensor"]} RSR')
        return()

    uoz = user_settings['uoz_default']
    uwv = user_settings['uwv_default']
    wind = user_settings['wind']
    pressure = user_settings['pressure']

    #load_ancillary_data : ['uoz', 'uwv', 'wind', 'pressure']
    global_attrs = load_ancillary_data(l1r, l1r_band_list, global_attrs, user_settings)

    ## elevation provided
    if user_settings['elevation'] is not None:
        user_settings['pressure'] = atmos.ac.pressure_elevation(user_settings['elevation'])
        global_attrs['pressure'] = user_settings['pressure']
        # print(global_attrs['pressure'])

    ## dem pressure
    if user_settings['dem_pressure']:
        # print(f'Extracting {user_settings["dem_source"]} DEM data')
        var_mem, l1r_band_list, global_attrs = get_dem_pressure(l1r, l1r_band_list, global_attrs, user_settings, var_mem)

    # print(f'default uoz: {user_settings["uoz_default"]:.2f} uwv: {user_settings["uwv_default"]:.2f} pressure: {user_settings["pressure_default"]:.2f}')
    # print(f'current uoz: {global_attrs["uoz"]:.2f} uwv: {global_attrs["uwv"]:.2f} pressure: {global_attrs["pressure"]:.2f}')

    ## which LUT data to read
    ro_type, global_attrs = select_lut_type(global_attrs, user_settings)

    ## get mean average geometry
    var_list = ['sza', 'vza', 'raa', 'pressure', 'wind']
    for l1r_band_str in l1r_band_list:
        if 'raa_' in l1r_band_list or 'vza_' in l1r_band_str:
            var_list.append(l1r_band_str)

    l1r = clip_angles(l1r, l1r_band_list, user_settings)
    var_mean = {k: np.nanmean(l1r[k]) if k in l1r_band_list else global_attrs[k] for k in var_list}
    var_mean = clip_angles_mean(var_mean, user_settings)

    ## get gas transmittance
    ### wave, h2o, o3, o2, co2, n2o, ch4, gas
    tg_dict = atmos.ac.gas_transmittance(var_mean['sza'], var_mean['vza'], uoz=global_attrs['uoz'], uwv=global_attrs['uwv'], rsr=rsrd['rsr'])

    ## make bands dataset
    ### add gases to band_ds
    band_table = prepare_attr_band_ds(band_table, rsrd, rhot_names, transmit_gas=tg_dict, user_settings=user_settings)
    del rhot_names, tg_dict

    ## select atmospheric correction method
    if user_settings['aerosol_correction'] == 'dark_spectrum':
        ac_opt = 'dsf'
    elif user_settings['aerosol_correction'] == 'exponential':
        ac_opt = 'exp'
    else:
        # print(f'Option aerosol_correction {user_settings["aerosol_correction"]} not configured')
        ac_opt = 'dsf'
    # print(f'Using {ac_opt.upper()} atmospheric correction')

    if user_settings['resolved_geometry'] and is_hyper:
        # print('Resolved geometry for hyperspectral sensors currently not supported')
        user_settings['resolved_geometry'] = False

    # prepare granule and environmental vars(sza, vza, raa, pressure, wind) and means of them in specific type(tile, segment, ...)
    var_mem, tiles, segment_data, use_rev_lut, per_pixel_geometry = build_l1r_mem(l1r, var_mean, var_list=var_list, l1r_band_list=l1r_band_list, rhot_bands=rhot_bands,
                                                                                  user_settings=user_settings, global_attrs=global_attrs, is_hyper=is_hyper)
    del var_mean

    t0 = time.time()
    # print(f'Loading LUTs {user_settings["luts"]}')

    ## load reverse lut romix -> aot
    rev_lut_table = None
    if use_rev_lut:
        rev_lut_table = atmos.aerlut.reverse_lut(global_attrs['sensor'], par=ro_type, rsky_lut=user_settings['dsf_interface_lut'], base_luts=user_settings['luts'])

    ## load aot -> atmospheric parameters lut
    ## QV 2022-04-04 interface reflectance is always loaded since we include wind in the interpolation below
    ## not necessary for runs with par == romix, to be fixed
    ### romix = mixed rho, rsky = sky rho, rsurf = surface rho
    lut_table = atmos.aerlut.import_luts(add_rsky=True, par=(ro_type if ro_type == 'romix+rsurf' else 'romix+rsky_t'), sensor=None if is_hyper else global_attrs['sensor'], rsky_lut_name=user_settings['dsf_interface_lut'],
                                         base_luts=user_settings['luts'], pressures=user_settings['luts_pressures'], reduce_dimensions=user_settings['luts_reduce_dimensions'])
    lut_mod_names = list(lut_table.keys())
    # print(f'Loading LUTs took {(time.time() - t0):.1f} s')

    gk = ''
    if ac_opt == 'dsf':
        aot_lut, aot_sel, aot_sel_par, aot_stack, aot_sel_bands, gk = apply_dsf(band_table=band_table, var_mem=var_mem, lut_table=lut_table, rsrd=rsrd, lut_mod_names=lut_mod_names, l1r_band_list=l1r_band_list,
                                                                                ro_type=ro_type, user_settings=user_settings, use_rev_lut=use_rev_lut, rev_lut_table=rev_lut_table,
                                                                                tiles=tiles, segment_data=segment_data, is_hyper=is_hyper)

        corr_func = partial(dsf_correction, aot_sel=aot_sel, aot_lut=aot_lut, rsrd=rsrd, lut_mod_names=lut_mod_names, lut_table=lut_table, var_mem=var_mem, segment_data=segment_data,
                            use_revlut=use_rev_lut, gk=gk, ro_type=ro_type, is_hyper=is_hyper)
    ## exponential
    elif ac_opt == 'exp':
        rhoam, xi, exp_lut, short_wv, long_wv, epsilon, mask, fixed_epsilon, fixed_rhoam, global_attrs = \
            apply_ac_exp(band_table=band_table, l1r_band_list=l1r_band_list, var_mem=var_mem, rsrd=rsrd, lut_mod_names=lut_mod_names, lut_table=lut_table, ro_type=ro_type,
                         user_settings=user_settings, global_attrs=global_attrs)

        corr_func = partial(exp_correction, lut_table=lut_table, ro_type=ro_type, rhoam=rhoam, xi=xi, exp_lut=exp_lut, short_wv=short_wv, long_wv=long_wv, epsilon=epsilon, mask=mask,
                            fixed_epsilon=fixed_epsilon, fixed_rhoam=fixed_rhoam)
    else:
        raise ValueError(f'Unknown atmospheric correction method {ac_opt}')

    ## set up interpolator for tiled processing
    if ac_opt == 'dsf':
        if user_settings['dsf_aot_estimate'] == 'tiled':
            xnew = np.linspace(0, tiles[-1][1], global_attrs['data_dimensions'][1], dtype=np.float32)
            ynew = np.linspace(0, tiles[-1][0], global_attrs['data_dimensions'][0], dtype=np.float32)

        ## store fixed aot in gatts
        if user_settings['dsf_aot_estimate'] == 'fixed':
            global_attrs['ac_aot_550'] = aot_sel[0][0]
            global_attrs['ac_model'] = lut_mod_names[aot_lut[0][0]]

            if user_settings['dsf_fixed_aot'] is None:
                ## store fitting parameter
                global_attrs['ac_fit'] = aot_sel_par[0][0]
                ## store bands used for DSF
                global_attrs['ac_bands'] = ','.join([str(b) for b in aot_stack[global_attrs['ac_model']]['band_list']])
                global_attrs['ac_nbands_fit'] = user_settings['dsf_nbands']
                for bbi, bn in enumerate(aot_sel_bands):
                    global_attrs['ac_band{}_idx'.format(bbi + 1)] = aot_sel_bands[bbi]
                    global_attrs['ac_band{}'.format(bbi + 1)] = aot_stack[global_attrs['ac_model']]['band_list'][aot_sel_bands[bbi]]

        ## write aot to outputfile
        if user_settings['dsf_write_aot_550']:
            ## reformat & save aot
            if user_settings['dsf_aot_estimate'] == 'fixed':
                aot_out = np.repeat(aot_sel, global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])
            elif user_settings['dsf_aot_estimate'] == 'segmented':
                aot_out = np.zeros(global_attrs['data_dimensions']) + np.nan
                for sidx, segment in enumerate(segment_data):
                    aot_out[segment_data[segment]['sub']] = aot_sel[sidx]
            elif user_settings['dsf_aot_estimate'] == 'tiled':
                aot_out = tiles_interp(aot_sel, xnew, ynew, target_mask=None,
                                                    smooth=user_settings['dsf_tile_smoothing'],
                                                    kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                    method=user_settings['dsf_tile_interp_method'])
            else:
                aot_out = aot_sel * 1.0
            ## write aot
            l2r['aot_550'] = aot_out
            l2r_band_list.append('aot_550')

    ## store ttot for glint correction
    # ttot_all = {}

    ## allow use of per pixel geometry for fixed dsf
    if per_pixel_geometry and (user_settings['dsf_aot_estimate'] == 'fixed') and (user_settings['resolved_geometry']):
        use_rev_lut = True

    ## for ease of subsetting later, repeat single element datasets to the tile shape
    if use_rev_lut and (ac_opt == 'dsf') and (user_settings['dsf_aot_estimate'] != 'tiled'):
        for ds in var_list:
            if len(np.atleast_1d(var_mem[ds])) != 1:
                continue

            # print(f'Reshaping {ds} to {global_attrs["data_dimensions"][0]}x{global_attrs["data_dimensions"][1]}')
            var_mem[ds] = np.repeat(var_mem[ds], global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])

    rho_cirrus = None
    ## figure out cirrus bands
    if user_settings['cirrus_correction']:
        rho_cirrus, l2r, l2r_band_list, user_settings = correct_cirrus(band_table=band_table, l1r_band_list=l1r_band_list, var_mem=var_mem,
                                                                       lut_mod_names=lut_mod_names, lut_table=lut_table, ro_type=ro_type, is_hyper=is_hyper, rsrd=rsrd,
                                                                       l2r=l2r, l2r_band_list=l2r_band_list, user_settings=user_settings)

    # print('use_revlut', use_revlut)
    calc_surface_reflectance(xnew=xnew, ynew=ynew, band_table=band_table, var_mem=var_mem, l1r_band_list=l1r_band_list,
                             gk=gk, lut_table=lut_table, rho_cirrus=rho_cirrus, ro_type=ro_type, use_revlut=use_rev_lut, segment_data=segment_data, is_hyper=is_hyper, ac_opt=ac_opt, luts=lut_mod_names, rsrd=rsrd,
                             l2r=l2r, l2r_band_list=l2r_band_list, rhos_to_band_name=rhos_to_band_name, corr_func=corr_func, global_attrs=global_attrs, user_settings=user_settings)

    ## glint correction
    if (ac_opt == 'dsf') and (user_settings['dsf_residual_glint_correction']) and (user_settings['dsf_residual_glint_correction_method'] == 'default'):
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
            sd = np.abs(b_v['att']['wave_nm'] - user_settings['glint_mask_rhos_wave'])
            if sd < 100:
                if sd < maskd:
                    gc_mask = b_v['att']['rhos_ds']
                    maskd = sd
                    gc_mask_b = band_slot
            ## user band
            if user_settings['glint_force_band'] is not None:
                sd = np.abs(b_v['att']['wave_nm'] - user_settings['glint_force_band'])
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
        if ((gc_swir1 is not None) and (gc_swir2 is not None)) or (gc_user is not None):
            t0 = time.time()
            print('Starting glint correction')

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
            refri_sen = atmos.shared.rsr_convolute_dict(refri['wave'] / 1000, refri['n'], rsrd['rsr'])

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
                sub_gc = np.where(np.isfinite(gc_mask_data) & (gc_mask_data <= user_settings['glint_mask_rhos_threshold']))
                del gc_mask_data

                ## get reference bands transmittance
                for ib, (band_slot, b_v) in enumerate(l2r['bands'].items()):
                    rhos_ds = b_v['att']['rhos_ds']
                    if rhos_ds not in [gc_swir1, gc_swir2, gc_user]:
                        continue
                    if rhos_ds not in l2r_datasets:
                        continue

                    ## two way direct transmittance
                    if user_settings['dsf_aot_estimate'] == 'tiled':
                        if user_settings['slicing']:
                            ## load rhos dataset
                            cur_data = l2r['bands'][band_slot]['data'].copy()
                            valid_mask = np.isfinite(cur_data)
                            del cur_data
                        ttot_all_b = atmos.shared.tiles_interp(ttot_all[band_slot], xnew, ynew,
                                                               target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                               target_mask_full=True,
                                                               smooth=user_settings['dsf_tile_smoothing'],
                                                               kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                               method=user_settings['dsf_tile_interp_method'])
                    elif user_settings['dsf_aot_estimate'] == 'segmented':
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
                    if rhos_ds not in l2r_datasets:
                        continue
                    if band_slot not in ttot_all:
                        continue
                    print(f'Performing glint correction for band {band_slot} ({b_v["att"]["wave_name"]} nm)')
                    ## load rhos dataset
                    cur_data = l2r['bands'][band_slot]['data'].copy()

                    ## two way direct transmittance
                    if user_settings['dsf_aot_estimate'] == 'tiled':
                        if user_settings['slicing']:
                            valid_mask = np.isfinite(cur_data)
                        ttot_all_b = atmos.shared.tiles_interp(ttot_all[band_slot], xnew, ynew,
                                                               target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                               target_mask_full=True,
                                                               smooth=user_settings['dsf_tile_smoothing'],
                                                               kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                               method=user_settings['dsf_tile_interp_method'])
                    elif user_settings['dsf_aot_estimate'] == 'segmented':
                        ttot_all_ = ttot_all[band_slot] * 1.0
                        ttot_all_b = np.zeros(global_attrs['data_dimensions']) + np.nan
                        for sidx, segment in enumerate(segment_data):
                            ttot_all_b[segment_data[segment]['sub']] = ttot_all_[sidx]
                        del ttot_all_
                    else:
                        ttot_all_b = ttot_all[band_slot] * 1.0
                    if user_settings['dsf_write_tiled_parameters']:
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
                        if user_settings['glint_write_rhog_ref']:
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
                    if user_settings['glint_write_rhog_all']:
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
        if (user_settings['dsf_aot_estimate'] == 'tiled') & (user_settings['slicing']):
            del valid_mask
    ## end glint correction

    ## alternative glint correction
    if (ac_opt == 'dsf') & (user_settings['dsf_residual_glint_correction']) & (user_settings['dsf_aot_estimate'] in ['fixed', 'segmented']) & \
            (user_settings['dsf_residual_glint_correction_method'] == 'alternative'):

        ## reference aot and wind speed
        if user_settings['dsf_aot_estimate'] == 'fixed':
            gc_aot = max(0.1, global_attrs['ac_aot_550'])
            gc_wind = 20
            gc_lut = global_attrs['ac_model']

            raa = global_attrs['raa']
            sza = global_attrs['sza']
            vza = global_attrs['vza']

            ## get surface reflectance for fixed geometry
            if len(np.atleast_1d(raa)) == 1:
                if hyper:
                    surf = lut_table[gc_lut]['rgi']((global_attrs['pressure'], lut_table[gc_lut]['ipd']['rsky_s'], lut_table[gc_lut]['meta']['wave'], raa, vza, sza, gc_wind, gc_aot))
                    surf_res = atmos.shared.rsr_convolute_dict(lut_table[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
                else:
                    surf_res = {b: lut_table[gc_lut]['rgi'][b]((global_attrs['pressure'], lut_table[gc_lut]['ipd']['rsky_s'], raa, vza, sza, gc_wind, gc_aot)) for b in lut_table[gc_lut]['rgi']}

        if user_settings['dsf_aot_estimate'] == 'segmented':
            for sidx, segment in enumerate(segment_data):
                gc_aot = max(0.1, aot_sel[sidx])
                gc_wind = 20
                gc_lut = lut_mod_names[aot_lut[sidx][0]]

                if sidx == 0:
                    surf_res = {}
                ## get surface reflectance for segmented geometry
                # if len(np.atleast_1d(raa)) == 1:
                if hyper:
                    surf = lut_table[gc_lut]['rgi'](
                        (var_mem['pressure' + gk][sidx], lut_table[gc_lut]['ipd']['rsky_s'], lut_table[gc_lut]['meta']['wave'],
                         var_mem['raa' + gk_raa][sidx], var_mem['vza' + gk_vza][sidx], var_mem['sza' + gk][sidx], gc_wind, gc_aot))

                    surf_res[segment] = atmos.shared.rsr_convolute_dict(lut_table[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
                else:
                    surf_res[segment] = {b: lut_table[gc_lut]['rgi'][b](
                        (var_mem['pressure' + gk][sidx], lut_table[gc_lut]['ipd']['rsky_s'], var_mem['raa' + gk_raa][sidx], var_mem['vza' + gk_vza][sidx],
                         var_mem['sza' + gk][sidx], gc_wind, gc_aot)
                    ) for b in lut_table[gc_lut]['rgi']}

        ## get reference surface reflectance
        gc_ref = None
        for ib, (band_slot, b_v) in enumerate(l2r["bands"].items()):
            band_num = band_slot[1:]
            rhos_ds = b_v['att']['rhos_ds']
            if rhos_ds not in l2r_datasets:
                continue
            if (b_v['att']['wavelength'] < user_settings['dsf_residual_glint_wave_range'][0]) | \
                    (b_v['att']['wavelength'] > user_settings['dsf_residual_glint_wave_range'][1]):
                continue

            print(f'Reading reference for glint correction from band {band_slot} ({b_v["att"]["wave_name"]} nm)')

            if user_settings['dsf_aot_estimate'] == 'fixed':
                gc_sur_cur = surf_res[band_num]
            if user_settings['dsf_aot_estimate'] == 'segmented':
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
            print(f'No bands found between {user_settings["dsf_residual_glint_wave_range"][0]} and {user_settings["dsf_residual_glint_wave_range"][1]} nm for glint correction')
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
            if user_settings['dsf_aot_estimate'] == 'segmented':
                axis = 2
            gc_sur_mean = np.nanmean(gc_sur, axis=axis)
            gc_sur_std = np.nanstd(gc_sur, axis=axis)

            ## get subset where to apply glint correction
            gc_sub = np.where(gc_ref_mean < user_settings['glint_mask_rhos_threshold'])

            ## glint correction per band
            for ib, (band_slot, b_v) in enumerate(l2r['bands'].items()):
                rhos_ds = b_v['att']['rhos_ds']
                band_name = band_slot[1:]
                if rhos_ds not in l2r_datasets:
                    continue
                print(f'Performing glint correction for band {band_slot} ({b_v["att"]["wave_name"]} nm)')

                ## estimate current band glint from reference glint image and ratio of interface reflectance
                if user_settings['dsf_aot_estimate'] == 'fixed':
                    sur = surf_res[band_name] * 1.0

                if user_settings['dsf_aot_estimate'] == 'segmented':
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
                if user_settings['glint_write_rhog_all']:
                    tmp = np.zeros(global_attrs['data_dimensions'], dtype=np.float32) + np.nan
                    tmp[gc_sub] = cur_rhog
                    rhog_key = f'rhog_{b_v["att"]["wave_name"]}'
                    l2r[rhog_key] = {}
                    l2r[rhog_key]['data'] = tmp
                    l2r[rhog_key]['att'] = {'wavelength': b_v['att']['wavelength']}
                    tmp = None
                cur_rhog = None
    ## end alternative glint correction

    return l2r
