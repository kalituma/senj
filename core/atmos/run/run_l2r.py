from functools import partial
import time
import numpy as np

from core import atmos
from core.util import tiles_interp, Logger
from core.atmos.setting import parse

from core.atmos.run.l2r import check_blackfill_skip, load_rsrd, load_ancillary_data, \
    get_dem_pressure, select_lut_type, clip_angles, clip_angles_mean, prepare_attr_band_ds, build_l1r_mem
from core.atmos.run.l2r.ac import apply_dsf, apply_ac_exp, correct_cirrus, correct_surface_reflectance, dsf_correction, exp_correction, \
    correct_glint, correct_glint_alt

def apply_l2r(l1r:dict, global_attrs:dict):

    Logger.get_logger().log('info', f'Start to build L2R for {global_attrs["sensor"]}')

    var_mem = {}
    l2r = {}
    l2r_band_list = []
    rhos_to_band_name = {}

    user_settings = parse(global_attrs['sensor'], settings=atmos.settings['user'])

    for k in user_settings:
        atmos.settings['run'][k] = user_settings[k]

    if user_settings['dsf_exclude_bands'] != None:
        if type(user_settings['dsf_exclude_bands']) != list:
            user_settings['dsf_exclude_bands'] = [user_settings['dsf_exclude_bands']]
    else:
        user_settings['dsf_exclude_bands'] = []

    band_table = l1r['bands'].copy()

    rhot_names = [band_table[key]['att']['parameter'] for key in band_table]
    rhot_bands = {
        rhot_name: band_table[key]['data'] for key, rhot_name in zip(band_table.keys(), rhot_names)
    }
    l1r_band_list = [key for key in l1r.keys() if key != 'bands'] + rhot_names

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
        Logger.get_logger().logger('info', f'Extracting {user_settings["dem_source"]} DEM data')
        var_mem, l1r_band_list, global_attrs = get_dem_pressure(l1r, l1r_band_list, global_attrs, user_settings, var_mem)

    Logger.get_logger().log('info',
                            f'default uoz: {user_settings["uoz_default"]:.2f} uwv: {user_settings["uwv_default"]:.2f} pressure: {user_settings["pressure_default"]:.2f}')
    Logger.get_logger().log('info',
                            f'current uoz: {global_attrs["uoz"]:.2f} uwv: {global_attrs["uwv"]:.2f} pressure: {global_attrs["pressure"]:.2f}')

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
        Logger.get_logger().log('info', f'Option aerosol_correction {user_settings["aerosol_correction"]} not configured')
        ac_opt = 'dsf'

    Logger.get_logger().log('info', f'Using {ac_opt.upper()} atmospheric correction')

    if user_settings['resolved_geometry'] and is_hyper:
        Logger.get_logger().log('info', 'Resolved geometry for hyperspectral sensors currently not supported')
        user_settings['resolved_geometry'] = False

    # prepare granule and environmental vars(sza, vza, raa, pressure, wind) and means of them in specific type(tile, segment, ...)
    var_mem, tiles, segment_data, use_rev_lut, per_pixel_geometry = build_l1r_mem(l1r, var_mean, var_list=var_list, l1r_band_list=l1r_band_list, rhot_bands=rhot_bands,
                                                                                  user_settings=user_settings, global_attrs=global_attrs, is_hyper=is_hyper)
    del var_mean

    t0 = time.time()
    Logger.get_logger().log('info', f'Loading LUTs {user_settings["luts"]}')

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
    Logger.get_logger().log('info', f'Loaded LUTs {user_settings["luts"]} in {(time.time() - t0):.1f} s')

    ttot_all = {}
    gk = ''
    if ac_opt == 'dsf':
        aot_lut, aot_sel, aot_stack, aot_sel_par, aot_sel_bands, gk = apply_dsf(band_table=band_table, var_mem=var_mem, lut_table=lut_table, rsrd=rsrd, lut_mod_names=lut_mod_names, l1r_band_list=l1r_band_list,
                                                                                ro_type=ro_type, user_settings=user_settings, use_rev_lut=use_rev_lut, rev_lut_table=rev_lut_table,
                                                                                tiles=tiles, segment_data=segment_data, is_hyper=is_hyper)

        corr_func = partial(dsf_correction, aot_sel=aot_sel, aot_lut=aot_lut, rsrd=rsrd, lut_mod_names=lut_mod_names, lut_table=lut_table,
                            var_mem=var_mem, segment_data=segment_data, ttot_all=ttot_all, use_revlut=use_rev_lut, gk=gk, ro_type=ro_type, is_hyper=is_hyper)
    ## exponential
    elif ac_opt == 'exp':
        rhoam, xi, exp_lut, short_wv, long_wv, epsilon, mask, fixed_epsilon, fixed_rhoam, global_attrs = \
            apply_ac_exp(band_table=band_table, l1r_band_list=l1r_band_list, var_mem=var_mem, rsrd=rsrd, lut_mod_names=lut_mod_names, lut_table=lut_table,
                         ro_type=ro_type,user_settings=user_settings, global_attrs=global_attrs)

        corr_func = partial(exp_correction, lut_table=lut_table, ro_type=ro_type, rhoam=rhoam, xi=xi, exp_lut=exp_lut, short_wv=short_wv,
                            long_wv=long_wv, epsilon=epsilon, mask=mask, fixed_epsilon=fixed_epsilon, fixed_rhoam=fixed_rhoam)
    else:
        raise ValueError(f'Unknown atmospheric correction method {ac_opt}')

    ## set up interpolator for tiled processing
    xnew, ynew = None, None
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
                aot_out = tiles_interp(aot_sel, xnew, ynew, target_mask=None, smooth=user_settings['dsf_tile_smoothing'], kern_size=user_settings['dsf_tile_smoothing_kernel_size'],
                                       method=user_settings['dsf_tile_interp_method'])
            else:
                aot_out = aot_sel * 1.0
            ## write aot
            l2r['aot_550'] = aot_out
            l2r_band_list.append('aot_550')

    ## store ttot for glint correction


    ## allow use of per pixel geometry for fixed dsf
    if per_pixel_geometry and (user_settings['dsf_aot_estimate'] == 'fixed') and (user_settings['resolved_geometry']):
        use_rev_lut = True

    ## for ease of subsetting later, repeat single element datasets to the tile shape
    if use_rev_lut and (ac_opt == 'dsf') and (user_settings['dsf_aot_estimate'] != 'tiled'):
        for ds in var_list:
            if len(np.atleast_1d(var_mem[ds])) != 1:
                continue

            Logger.get_logger().log('info', f'Reshaping {ds} to {global_attrs["data_dimensions"][0]}x{global_attrs["data_dimensions"][1]}')
            var_mem[ds] = np.repeat(var_mem[ds], global_attrs['data_elements']).reshape(global_attrs['data_dimensions'])

    rho_cirrus = None
    ## figure out cirrus bands
    if user_settings['cirrus_correction']:
        rho_cirrus, l2r, l2r_band_list, user_settings = correct_cirrus(band_table=band_table, l1r_band_list=l1r_band_list, var_mem=var_mem,
                                                                       lut_mod_names=lut_mod_names, lut_table=lut_table, ro_type=ro_type, is_hyper=is_hyper, rsrd=rsrd,
                                                                       l2r=l2r, l2r_band_list=l2r_band_list, user_settings=user_settings)

    # print('use_revlut', use_revlut)
    l2r, l2r_band_list, rhos_to_band_name, gk_vza, gk_raa =\
        correct_surface_reflectance(xnew=xnew, ynew=ynew, band_table=band_table, var_mem=var_mem,
                                    l1r_band_list=l1r_band_list, gk=gk, lut_table=lut_table, rho_cirrus=rho_cirrus,
                                    ro_type=ro_type, use_revlut=use_rev_lut, segment_data=segment_data,
                                    is_hyper=is_hyper, ac_opt=ac_opt, luts=lut_mod_names, rsrd=rsrd, corr_func=corr_func,
                                    global_attrs=global_attrs, user_settings=user_settings, l2r=l2r, l2r_band_list=l2r_band_list, rhos_to_band_name=rhos_to_band_name)
    if ac_opt == 'dsf':
        if user_settings['dsf_residual_glint_correction']:
            ## glint correction
            if user_settings['dsf_residual_glint_correction_method'] == 'default':
                l2r = correct_glint(l1r, rsrd=rsrd, xnew=xnew, ynew=ynew, segment_data=segment_data, ttot_all=ttot_all, l2r=l2r, l2r_band_list=l2r_band_list,
                                    rhos_to_band_name=rhos_to_band_name, user_settings=user_settings, global_attrs=global_attrs)

            ## alternative glint correction
            if user_settings['dsf_residual_glint_correction_method'] == 'alternative' and (user_settings['dsf_aot_estimate'] in ['fixed', 'segmented']):
                l2r = correct_glint_alt(l2r, aot_sel=aot_sel, aot_lut=aot_lut, var_mem=var_mem, lut_mod_names=lut_mod_names, lut_table=lut_table,
                                        l2r_band_list=l2r_band_list, rsrd=rsrd, segment_data=segment_data, gk=gk, gk_raa=gk_raa, gk_vza=gk_vza, is_hyper=is_hyper,
                                        user_settings=user_settings, global_attrs=global_attrs)


    return l2r, global_attrs
