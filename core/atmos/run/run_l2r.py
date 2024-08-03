import os, time, datetime
import numpy as np
import scipy.ndimage, scipy.interpolate
import skimage.measure

from core import atmos
from core.atmos.setting import parse
from core.atmos.run.l2r import check_blackfill_skip, load_rsrd, load_ancillary_data, \
    get_dem_pressure, select_lut_type, clip_angles, prepare_attr_band_ds, build_l1r_mem, \
    apply_dsf


def apply_l2r(l1r:dict, global_attrs:dict):

    data_mem = {}
    # l2r = {}
    # rhos_to_band_name = {}
    # l2r['bands'] = {}
    # l2r['inputs'] = {}
    #
    # l2r_datasets = []

    user_settings = parse(global_attrs['sensor'], settings=atmos.settings['user'])

    for k in user_settings:
        atmos.settings['run'][k] = user_settings[k]

    if user_settings['dsf_exclude_bands'] != None:
        if type(user_settings['dsf_exclude_bands']) != list:
            user_settings['dsf_exclude_bands'] = [user_settings['dsf_exclude_bands']]
    else:
        user_settings['dsf_exclude_bands'] = []

    band_ds = l1r['bands'].copy()
    rhot_names = [band_ds[key]['att']['rhot_ds'] for key in band_ds]
    rhot_bands = {
        rhot_name: band_ds[key]['data'] for key, rhot_name in zip(band_ds.keys(), rhot_names)
    }
    l1r_ds = list(l1r.keys())[:-1] + rhot_names

    if user_settings['blackfill_skip']:
        if check_blackfill_skip(band_ds, user_settings):
            return ()

    # print(f'Running acolite for {setu["inputfile"]}')

    first_band_key = list(band_ds.keys())[-1]
    global_attrs['data_dimensions'] = band_ds[first_band_key]['data'].shape
    global_attrs['data_elements'] = global_attrs['data_dimensions'][0] * global_attrs['data_dimensions'][1]

    rsrd, is_hyper = load_rsrd(global_attrs)

    if global_attrs['sensor'] in rsrd:
        rsrd = rsrd[global_attrs['sensor']]
    else:
        print(f'Could not find {global_attrs["sensor"]} RSR')
        return()

    # gatts['uoz'] = setu['uoz_default']
    # gatts['uwv'] = setu['uwv_default']
    # gatts['wind'] = setu['wind']
    # gatts['pressure'] = setu['pressure']

    uoz = user_settings['uoz_default']
    uwv = user_settings['uwv_default']
    wind = user_settings['wind']
    pressure = user_settings['pressure']

    #load_ancillary_data : ['uoz', 'uwv', 'wind', 'pressure']
    global_attrs = load_ancillary_data(l1r, l1r_ds, global_attrs, user_settings)

    ## elevation provided
    if user_settings['elevation'] is not None:
        user_settings['pressure'] = atmos.ac.pressure_elevation(user_settings['elevation'])
        global_attrs['pressure'] = user_settings['pressure']
        # print(global_attrs['pressure'])

    ## dem pressure
    if user_settings['dem_pressure']:
        # print(f'Extracting {user_settings["dem_source"]} DEM data')
        l1r, l1r_ds, global_attrs = get_dem_pressure(l1r, l1r_ds, global_attrs, user_settings)

    # print(f'default uoz: {user_settings["uoz_default"]:.2f} uwv: {user_settings["uwv_default"]:.2f} pressure: {user_settings["pressure_default"]:.2f}')
    # print(f'current uoz: {global_attrs["uoz"]:.2f} uwv: {global_attrs["uwv"]:.2f} pressure: {global_attrs["pressure"]:.2f}')

    ## which LUT data to read
    par, global_attrs = select_lut_type(global_attrs, user_settings)

    ## get mean average geometry
    mean_ds = ['sza', 'vza', 'raa', 'pressure', 'wind']
    for l1r_band_str in l1r_ds:
        if ('raa_' in l1r_ds) or ('vza_' in l1r_band_str):
            mean_ds.append(l1r_band_str)

    geom_mean = {k: np.nanmean(l1r[k]) if k in l1r_ds else global_attrs[k] for k in mean_ds}

    l1r, geom_mean = clip_angles(l1r_ds, l1r, geom_mean, user_settings)

    ## get gas transmittance
    tg_dict = atmos.ac.gas_transmittance(geom_mean['sza'], geom_mean['vza'],
                                         uoz=global_attrs['uoz'], uwv=global_attrs['uwv'],
                                         rsr=rsrd['rsr'])

    ## make bands dataset
    band_ds = prepare_attr_band_ds(band_ds, rsrd, user_settings, rhot_names, transmit_gas=tg_dict)

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

    data_mem, use_revlut, per_pixel_geometry = build_l1r_mem(l1r, geom_mean, mean_ds=mean_ds, l1r_ds=l1r_ds,
                                                             rhot_bands=rhot_bands, user_settings=user_settings,
                                                             global_attrs=global_attrs, is_hyper=is_hyper)

    ## do not allow LUT boundaries ()
    left, right = np.nan, np.nan
    if user_settings['dsf_allow_lut_boundaries']:
        left, right = None, None

    t0 = time.time()
    # print(f'Loading LUTs {user_settings["luts"]}')

    ## load reverse lut romix -> aot
    if use_revlut:
        revl = atmos.aerlut.reverse_lut(global_attrs['sensor'], par=par, rsky_lut=user_settings['dsf_interface_lut'], base_luts=user_settings['luts'])

    ## load aot -> atmospheric parameters lut
    ## QV 2022-04-04 interface reflectance is always loaded since we include wind in the interpolation below
    ## not necessary for runs with par == romix, to be fixed
    lutdw = atmos.aerlut.import_luts(add_rsky=True, par=(par if par == 'romix+rsurf' else 'romix+rsky_t'),
                                     sensor=None if is_hyper else global_attrs['sensor'],
                                     rsky_lut=user_settings['dsf_interface_lut'],
                                     base_luts=user_settings['luts'], pressures=user_settings['luts_pressures'],
                                     reduce_dimensions=user_settings['luts_reduce_dimensions'])
    luts = list(lutdw.keys())
    # print(f'Loading LUTs took {(time.time() - t0):.1f} s')

    ## #####################
    ## dark spectrum fitting
    aot_lut = None
    aot_sel= None
    aot_sel_lut = None
    aot_sel_par = None

    if ac_opt == 'dsf':
        apply_dsf()

    ## exponential
    elif ac_opt == 'exp':
        ## find bands to use
        exp_b1 = None
        exp_b1_diff = 1000
        exp_b2 = None
        exp_b2_diff = 1000
        exp_mask = None
        exp_mask_diff = 1000

        for band_slot, b_v in l1r['bands'].items():
            sd = np.abs(b_v['att']['wave_nm'] - user_settings['exp_wave1'])
            if (sd < 100) & (sd < exp_b1_diff):
                exp_b1_diff = sd
                exp_b1 = band_slot
                short_wv = b_v['att']['wave_nm']
            sd = np.abs(b_v['att']['wave_nm'] - user_settings['exp_wave2'])
            if (sd < 100) & (sd < exp_b2_diff):
                exp_b2_diff = sd
                exp_b2 = band_slot
                long_wv = b_v['att']['wave_nm']
            sd = np.abs(b_v['att']['wave_nm'] - user_settings['l2w_mask_wave'])
            if (sd < 100) & (sd < exp_mask_diff):
                exp_mask_diff = sd
                exp_mask = band_slot
                mask_wv = b_v['att']['wave_nm']

        if (exp_b1 is None) or (exp_b2 is None):
            raise ValueError('Stopped: EXP bands not found in L1R bands')

        print(f'Selected bands {exp_b1} and {exp_b2} for EXP processing')
        if (l1r['bands'][exp_b1]['att']['rhot_ds'] not in l1r_datasets) | (l1r['bands'][exp_b2]['att']['rhot_ds'] not in l1r_datasets):
            print(f'Selected bands are not available in {user_settings["inputfile"]}')
            if (l1r['bands'][exp_b1]['att']['rhot_ds'] not in l1r_datasets):
                print(f'EXP B1: {l1r["bands"][exp_b1]["att"]["rhot_ds"]}')
            if (l1r['bands'][exp_b2]['att']['rhot_ds'] not in l1r_datasets):
                print(f'EXP B2: {l1r["bands"][exp_b2]["att"]["rhot_ds"]}')
            return ()

        ## determine processing option
        if (short_wv < 900) & (long_wv < 900):
            exp_option = 'red/NIR'
        elif (short_wv < 900) & (long_wv > 1500):
            exp_option = 'NIR/SWIR'
        else:
            exp_option = 'SWIR'

        ## read data
        exp_d1 = l1r['bands'][exp_b1]['data'] * 1.0
        exp_d2 = l1r['bands'][exp_b2]['data'] * 1.0

        ## use mean geometry
        xi = [data_mem['pressure' + '_mean'][0][0],
              data_mem['raa' + '_mean'][0][0],
              data_mem['vza' + '_mean'][0][0],
              data_mem['sza' + '_mean'][0][0],
              data_mem['wind' + '_mean'][0][0]]

        exp_lut = luts[0]
        exp_cwlim = 0.005
        exp_initial_epsilon = 1.0

        ## Rayleigh reflectance
        rorayl_b1 = lutdw[exp_lut]['rgi'][exp_b1]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
        rorayl_b2 = lutdw[exp_lut]['rgi'][exp_b2]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))

        ## subtract Rayleigh reflectance
        exp_d1 -= rorayl_b1
        exp_d2 -= rorayl_b2

        ## compute mask
        if exp_mask == exp_b1:
            mask = exp_d1 >= user_settings['exp_swir_threshold']
        elif exp_mask == exp_b2:
            mask = exp_d2 >= user_settings['exp_swir_threshold']
        else:
            exp_dm = l1r["bands"][exp_mask]["data"] * 1.0
            rorayl_mask = lutdw[exp_lut]['rgi'][exp_mask]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
            exp_dm -= rorayl_mask
            mask = exp_dm >= user_settings['exp_swir_threshold']
            exp_dm = None

        ## compute aerosol epsilon band ratio
        epsilon = exp_d1 / exp_d2
        epsilon[np.where(mask)] = np.nan

        ## red/NIR option
        exp_fixed_epsilon = False
        if user_settings['exp_fixed_epsilon']:
            exp_fixed_epsilon = True

        if exp_option == 'red/NIR':
            print('Using similarity spectrum for red/NIR EXP')
            exp_fixed_epsilon = True

            ## Rayleigh transmittances in both bands
            dtotr_b1 = lutdw[exp_lut]['rgi'][exp_b1]((xi[0], lutdw[exp_lut]['ipd']['dtott'], xi[1], xi[2], xi[3], xi[4], 0.001))
            utotr_b1 = lutdw[exp_lut]['rgi'][exp_b1]((xi[0], lutdw[exp_lut]['ipd']['utott'], xi[1], xi[2], xi[3], xi[4], 0.001))
            dtotr_b2 = lutdw[exp_lut]['rgi'][exp_b2]((xi[0], lutdw[exp_lut]['ipd']['dtott'], xi[1], xi[2], xi[3], xi[4], 0.001))
            utotr_b2 = lutdw[exp_lut]['rgi'][exp_b2]((xi[0], lutdw[exp_lut]['ipd']['utott'], xi[1], xi[2], xi[3], xi[4], 0.001))
            tr_b1 = (dtotr_b1 * utotr_b1 * l1r['bands'][exp_b1]['att']['tt_gas'])
            tr_b2 = (dtotr_b2 * utotr_b2 * l1r['bands'][exp_b2]['att']['tt_gas'])
            ## get gamma
            exp_gamma = tr_b1 / tr_b2 if user_settings['exp_gamma'] is None else float(user_settings['exp_gamma'])
            print(f'Gamma: {exp_gamma:.2f}')

            ## get alpha
            if user_settings['exp_alpha'] is None:
                ## import simspec
                simspec = atmos.shared.similarity_read()
                ## convolute to sensor_o
                if user_settings['exp_alpha_weighted']:
                    ssd = atmos.shared.rsr_convolute_dict(simspec['wave'], simspec['ave'], rsrd['rsr'])
                    exp_alpha = ssd[exp_b1] / ssd[exp_b2]
                ## or use closest bands
                else:
                    ssi0, ssw0 = atmos.shared.closest_idx(simspec['wave'], l1r['bands'][exp_b1]['att']['wave_mu'])
                    ssi1, ssw1 = atmos.shared.closest_idx(simspec['wave'], l1r['bands'][exp_b2]['att']['wave_mu'])
                    exp_alpha = simspec['ave'][ssi0] / simspec['ave'][ssi1]
            else:
                exp_alpha = float(user_settings['exp_alpha'])
            print(f'Alpha: {exp_alpha:.2f}')

            ## first estimate of rhow to find clear waters
            exp_c1 = (exp_alpha / tr_b2) / (exp_alpha * exp_gamma - exp_initial_epsilon)
            exp_c2 = exp_initial_epsilon * exp_c1
            rhow_short = (exp_c1 * exp_d1) - (exp_c2 * exp_d2)

            ## additional masking for epsilon
            epsilon[(rhow_short < 0.) & (rhow_short > exp_cwlim)] = np.nan
            rhow_short = None

        elif exp_option == 'NIR/SWIR':
            print('Using NIR/SWIR EXP')
            exp_fixed_epsilon = True
            ## additional masking for epsilon
            mask2 = (exp_d2 < ((exp_d1 + 0.005) * 1.5)) & \
                    (exp_d2 > ((exp_d1 - 0.005) * 0.8)) & \
                    ((exp_d2 + 0.005) / exp_d1 > 0.8)
            epsilon[mask2] = np.nan
            mask2 = None
        elif exp_option == 'SWIR':
            print('Using SWIR EXP')
            if user_settings['exp_fixed_aerosol_reflectance']: exp_fixed_epsilon = True

        ## compute fixed epsilon
        if exp_fixed_epsilon:
            if user_settings['exp_epsilon'] is not None:
                epsilon = float(user_settings['exp_epsilon'])
            else:
                epsilon = np.nanpercentile(epsilon, user_settings['exp_fixed_epsilon_percentile'])

        ## determination of rhoam in long wavelength
        if exp_option == 'red/NIR':
            rhoam = (exp_alpha * exp_gamma * exp_d2 - exp_d1) / (exp_alpha * exp_gamma - epsilon)
        else:
            rhoam = exp_d2 * 1.0

        ## clear memory
        exp_d1, exp_d2 = None, None

        ## fixed rhoam?
        exp_fixed_rhoam = user_settings['exp_fixed_aerosol_reflectance']
        if exp_fixed_rhoam:
            rhoam = np.nanpercentile(rhoam, user_settings['exp_fixed_aerosol_reflectance_percentile'])
            print(f'{user_settings["exp_fixed_aerosol_reflectance_percentile"]:.0f}th percentile rhoam ({long_wv} nm): {rhoam:.5f}')

        print('EXP band 1', user_settings['exp_wave1'], exp_b1, l1r['bands'][exp_b1]['att']['rhot_ds'])
        print('EXP band 2', user_settings['exp_wave2'], exp_b2, l1r['bands'][exp_b2]['att']['rhot_ds'])

        if exp_fixed_epsilon:
            print(f'Epsilon: {epsilon:.2f}')

        ## output data
        if user_settings['exp_output_intermediate']:
            if not exp_fixed_epsilon:
                global_attrs['epsilon'] = epsilon
            if not exp_fixed_rhoam:
                global_attrs['rhoam'] = rhoam
    ## end exponential

    ## set up interpolator for tiled processing
    if (ac_opt == 'dsf') & (user_settings['dsf_aot_estimate'] == 'tiled'):
        xnew = np.linspace(0, tiles[-1][1], global_attrs['data_dimensions'][1], dtype=np.float32)
        ynew = np.linspace(0, tiles[-1][0], global_attrs['data_dimensions'][0], dtype=np.float32)

    ## store fixed aot in gatts
    if (ac_opt == 'dsf') & (user_settings['dsf_aot_estimate'] == 'fixed'):
        global_attrs['ac_aot_550'] = aot_sel[0][0]
        global_attrs['ac_model'] = luts[aot_lut[0][0]]

        if user_settings['dsf_fixed_aot'] is None:
            ## store fitting parameter
            global_attrs['ac_fit'] = aot_sel_par[0][0]
            ## store bands used for DSF
            global_attrs['ac_bands'] = ','.join([str(b) for b in aot_stack[global_attrs['ac_model']]['band_list']])
            global_attrs['ac_nbands_fit'] = user_settings['dsf_nbands']
            for bbi, bn in enumerate(aot_sel_bands):
                global_attrs['ac_band{}_idx'.format(bbi + 1)] = aot_sel_bands[bbi]
                global_attrs['ac_band{}'.format(bbi + 1)] = aot_stack[global_attrs['ac_model']]['band_list'][
                    aot_sel_bands[bbi]]

    ## write aot to outputfile
    if (ac_opt == 'dsf') & (user_settings['dsf_write_aot_550']):
        ## reformat & save aot
        if user_settings['dsf_aot_estimate'] == 'fixed':
            aot_out = np.repeat(aot_sel, global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])
        elif user_settings['dsf_aot_estimate'] == 'segmented':
            aot_out = np.zeros(global_attrs['data_dimensions']) + np.nan
            for sidx, segment in enumerate(segment_data):
                aot_out[segment_data[segment]['sub']] = aot_sel[sidx]
        elif user_settings['dsf_aot_estimate'] == 'tiled':
            aot_out = atmos.shared.tiles_interp(aot_sel, xnew, ynew, target_mask=None,
                                                smooth=user_settings['dsf_tile_smoothing'],
                                                kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                method=user_settings['dsf_tile_interp_method'])
        else:
            aot_out = aot_sel * 1.0
        ## write aot
        l2r['aot_550'] = aot_out
        l2r_datasets.append('aot_550')

    ## store ttot for glint correction
    ttot_all = {}

    ## allow use of per pixel geometry for fixed dsf
    if (per_pixel_geometry) & (user_settings['dsf_aot_estimate'] == 'fixed') & (user_settings['resolved_geometry']):
        use_revlut = True

    ## for ease of subsetting later, repeat single element datasets to the tile shape
    if (use_revlut) & (ac_opt == 'dsf') & (user_settings['dsf_aot_estimate'] != 'tiled'):
        for ds in mean_ds:
            if len(np.atleast_1d(data_mem[ds])) != 1:
                continue

            print(f'Reshaping {ds} to {global_attrs["data_dimensions"][0]}x{global_attrs["data_dimensions"][1]}')
            data_mem[ds] = np.repeat(data_mem[ds], global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])

    ## figure out cirrus bands
    if user_settings['cirrus_correction']:
        rho_cirrus = None

        ## use mean geometry to compute cirrus band Rayleigh
        xi = [data_mem['pressure' + '_mean'][0][0],
              data_mem['raa' + '_mean'][0][0],
              data_mem['vza' + '_mean'][0][0],
              data_mem['sza' + '_mean'][0][0],
              data_mem['wind' + '_mean'][0][0]]

        ## compute Rayleigh reflectance for hyperspectral sensors
        if hyper:
            rorayl_hyp = lutdw[luts[0]]['rgi']((xi[0], lutdw[luts[0]]['ipd'][par],
                                                lutdw[luts[0]]['meta']['wave'], xi[1], xi[2], xi[3], xi[4],
                                                0.001)).flatten()

        ## find cirrus bands
        for bi, band_slot, b_v in enumerate(l1r['bands'].items()):
            band_num = band_slot[1:]
            if ('rhot_ds' not in b_v['att']):
                continue
            if b_v['att']['rhot_ds'] not in l1r_datasets:
                continue
            if (b_v['att']['wave_nm'] < user_settings['cirrus_range'][0]):
                continue
            if (b_v['att']['wave_nm'] > user_settings['cirrus_range'][1]):
                continue

            ## compute Rayleigh reflectance
            if hyper:
                rorayl_cur = atmos.shared.rsr_convolute_nd(rorayl_hyp, lutdw[luts[0]]['meta']['wave'],
                                                           rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'], axis=0)
            else:
                rorayl_cur = lutdw[luts[0]]['rgi'][band_slot]((xi[0], lutdw[luts[0]]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))

            ## cirrus reflectance = rho_t - rho_Rayleigh
            cur_data = l1r['bands'][band_slot]['data'] - rorayl_cur

            if rho_cirrus is None:
                rho_cirrus = cur_data * 1.0
            else:
                rho_cirrus = np.dstack((rho_cirrus, cur_data))
            cur_data = None

        if rho_cirrus is None:
            user_settings['cirrus_correction'] = False
        else:
            ## compute mean from several bands
            if len(rho_cirrus.shape) == 3:
                rho_cirrus = np.nanmean(rho_cirrus, axis=2)
            ## write cirrus mean
            l2r['rho_cirrus'] = rho_cirrus
            l2r_datasets.append('rho_cirrus')

    print('use_revlut', use_revlut)

    hyper_res = None
    ## compute surface reflectances
    for bi, (band_slot, b_v) in enumerate(l1r['bands'].items()):
        band_num = band_slot[1:]
        if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm not in bands dataset')
            continue
        if b_v['att']['rhot_ds'] not in l1r_datasets:
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm not in available rhot datasets')
            continue  ## skip if we don't have rhot for a band that is in the RSR file

        ## temporary fix
        if b_v['att']['wave_mu'] < 0.345:
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm wavelength < 345 nm')
            continue  ## skip if below LUT range

        rhot_name = b_v['att']['rhot_ds'] # dsi
        rhos_name = b_v['att']['rhos_ds'] # dso
        cur_data, cur_att = b_v['data'].copy(), b_v['att'].copy()

        ## store rhot in output file

        if b_v['att']['tt_gas'] < user_settings['min_tgas_rho']:
            print(f'Band {band_slot} at {b_v["att"]["wave_name"]} nm has tgas < min_tgas_rho ({b_v["att"]["tt_gas"]:.2f} < {user_settings["min_tgas_rho"]:.2f})')
            continue

        ## apply cirrus correction
        if user_settings['cirrus_correction']:
            g = user_settings['cirrus_g_vnir'] * 1.0
            if b_v['att']['wave_nm'] > 1000:
                g = user_settings['cirrus_g_swir'] * 1.0
            cur_data -= (rho_cirrus * g)

        t0 = time.time()
        print('Computing surface reflectance', band_slot, b_v['att']['wave_name'],f'{b_v["att"]["tt_gas"]:.3f}')

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

            if (user_settings['dsf_residual_glint_correction']) & (user_settings['dsf_residual_glint_correction_method'] == 'default'):
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
                    romix[ls] = atmos.shared.rsr_convolute_nd(hyper_res[par], lutdw[lut]['meta']['wave'],
                                                           rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'], axis=0)
                    ## transmittance and spherical albedo
                    astot[ls] = atmos.shared.rsr_convolute_nd(hyper_res['astot'], lutdw[lut]['meta']['wave'],
                                                           rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'], axis=0)
                    dutott[ls] = atmos.shared.rsr_convolute_nd(hyper_res['dutott'], lutdw[lut]['meta']['wave'],
                                                            rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'], axis=0)

                    ## total transmittance
                    if (user_settings['dsf_residual_glint_correction']) & (
                            user_settings['dsf_residual_glint_correction_method'] == 'default'):
                        ttot_all[band_slot][ls] = atmos.shared.rsr_convolute_nd(hyper_res['ttot'], lutdw[lut]['meta']['wave'],
                                                                     rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'],
                                                                     axis=0)
                else:
                    ## path reflectance
                    romix[ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], ai))

                    ## transmittance and spherical albedo
                    astot[ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd']['astot'], xi[1], xi[2], xi[3], xi[4], ai))
                    dutott[ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], ai))

                    ## total transmittance
                    if (user_settings['dsf_residual_glint_correction']) & (user_settings['dsf_residual_glint_correction_method'] == 'default'):
                        ttot_all[band_slot][ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd']['ttot'], xi[1], xi[2], xi[3], xi[4], ai))
                del ls, ai, xi

            ## interpolate tiled processing to full scene
            if user_settings['dsf_aot_estimate'] == 'tiled':
                print('Interpolating tiles')
                romix = atmos.shared.tiles_interp(romix, xnew, ynew, target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                  target_mask_full=True, smooth=user_settings['dsf_tile_smoothing'],
                                                  kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                  method=user_settings['dsf_tile_interp_method'])
                astot = atmos.shared.tiles_interp(astot, xnew, ynew, target_mask=(valid_mask if user_settings['slicing'] else None), \
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
            rorayl_cur = lutdw[exp_lut]['rgi'][band_num]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
            dutotr_cur = lutdw[exp_lut]['rgi'][band_num]((xi[0], lutdw[exp_lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], 0.001))

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
                    rorayl_hyper = lutdw[luts[0]]['rgi']((xi[0], lutdw[luts[0]]['ipd'][par],lutdw[luts[0]]['meta']['wave'], xi[1], xi[2], xi[3],xi[4], 0.001)).flatten()
                    dutotr_hyper = lutdw[luts[0]]['rgi']((xi[0], lutdw[luts[0]]['ipd']['dutott'],lutdw[luts[0]]['meta']['wave'], xi[1], xi[2], xi[3],xi[4], 0.001)).flatten()
                    rorayl_cur = atmos.shared.rsr_convolute_nd(rorayl_hyper, lutdw[luts[0]]['meta']['wave'],rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'],axis=0)
                    dutotr_cur = atmos.shared.rsr_convolute_nd(dutotr_hyper, lutdw[luts[0]]['meta']['wave'],rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'],axis=0)
                    del rorayl_hyper, dutotr_hyper
                else:
                    rorayl_cur = lutdw[luts[0]]['rgi'][band_num]((xi[0], lutdw[luts[0]]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
                    dutotr_cur = lutdw[luts[0]]['rgi'][band_num]((xi[0], lutdw[luts[0]]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], 0.001))

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
                                                       target_mask_full=True, smooth=user_settings['dsf_tile_smoothing'],
                                                       kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                                       method=user_settings['dsf_tile_interp_method'])
                dutotr_cur = atmos.shared.tiles_interp(dutotr_cur, xnew, ynew,
                                                       target_mask=(valid_mask if user_settings['slicing'] else None), \
                                                       target_mask_full=True, smooth=user_settings['dsf_tile_smoothing'],
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
        print(f'{global_attrs["sensor"]}/{band_slot} took {(time.time() - t0):.1f}s ({"RevLUT" if use_revlut else "StdLUT"})')

    ## glint correction
    if (ac_opt == 'dsf') & (user_settings['dsf_residual_glint_correction']) & (user_settings['dsf_residual_glint_correction_method'] == 'default'):
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
                    surf = lutdw[gc_lut]['rgi']((global_attrs['pressure'], lutdw[gc_lut]['ipd']['rsky_s'], lutdw[gc_lut]['meta']['wave'], raa, vza, sza, gc_wind, gc_aot))
                    surf_res = atmos.shared.rsr_convolute_dict(lutdw[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
                else:
                    surf_res = {b: lutdw[gc_lut]['rgi'][b]((global_attrs['pressure'], lutdw[gc_lut]['ipd']['rsky_s'], raa, vza, sza, gc_wind, gc_aot)) for b in lutdw[gc_lut]['rgi']}

        if user_settings['dsf_aot_estimate'] == 'segmented':
            for sidx, segment in enumerate(segment_data):
                gc_aot = max(0.1, aot_sel[sidx])
                gc_wind = 20
                gc_lut = luts[aot_lut[sidx][0]]

                if sidx == 0:
                    surf_res = {}
                ## get surface reflectance for segmented geometry
                # if len(np.atleast_1d(raa)) == 1:
                if hyper:
                    surf = lutdw[gc_lut]['rgi'](
                        (data_mem['pressure' + gk][sidx], lutdw[gc_lut]['ipd']['rsky_s'], lutdw[gc_lut]['meta']['wave'],
                         data_mem['raa' + gk_raa][sidx], data_mem['vza' + gk_vza][sidx], data_mem['sza' + gk][sidx], gc_wind, gc_aot))

                    surf_res[segment] = atmos.shared.rsr_convolute_dict(lutdw[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
                else:
                    surf_res[segment] = {b: lutdw[gc_lut]['rgi'][b](
                        (data_mem['pressure' + gk][sidx], lutdw[gc_lut]['ipd']['rsky_s'], data_mem['raa' + gk_raa][sidx], data_mem['vza' + gk_vza][sidx],
                         data_mem['sza' + gk][sidx], gc_wind, gc_aot)
                    ) for b in lutdw[gc_lut]['rgi']}

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
