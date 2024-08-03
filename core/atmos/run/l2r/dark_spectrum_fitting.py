import numpy as np
import scipy.ndimage, scipy.interpolate

def apply_dsf(band_ds, luts, l1r_ds, user_settings:dict, use_revlut:bool):
    ## #####################
    ## dark spectrum fitting
    aot_lut = None
    aot_sel = None
    aot_sel_lut = None
    aot_sel_par = None

    ## user supplied aot
    if user_settings['dsf_fixed_aot'] is not None:
        user_settings['dsf_aot_estimate'] = 'fixed'
        aot_lut = None
        for l_i, lut_name in enumerate(luts):
            if lut_name == user_settings['dsf_fixed_lut']:
                aot_lut = np.array(l_i)
                aot_lut.shape += (1, 1)  ## make 1,1 dimensions
        if aot_lut is None:
            print(f'LUT {user_settings["dsf_fixed_lut"]} not recognised')

        aot_sel = np.array(float(user_settings['dsf_fixed_aot']))
        aot_sel.shape += (1, 1)  ## make 1,1 dimensions
        aot_sel_lut = luts[aot_lut[0][0]]
        aot_sel_par = None
        print(f'User specified aot {aot_sel[0][0]} and model {aot_sel_lut}')

        ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
        gk = '' if use_revlut else '_mean'
    ## image derived aot
    else:
        if user_settings['dsf_spectrum_option'] not in ['darkest', 'percentile', 'intercept']:
            # print('dsf_spectrum_option {} not configured, falling back to darkest'.format(user_settings['dsf_spectrum_option']))
            user_settings['dsf_spectrum_option'] = 'darkest'

        rhot_aot = None
        ## run through bands to get aot
        aot_bands = []
        aot_dict = {}
        dsf_rhod = {}
        for bi, (band_slot, b_v) in enumerate(band_ds.items()):
            if (band_slot in user_settings['dsf_exclude_bands']):
                continue
            if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
                continue
            if b_v['att']['rhot_ds'] not in l1r_ds:
                continue

            ## skip band for aot computation
            if b_v['att']['tt_gas'] < user_settings['min_tgas_aot']:
                continue

            ## skip bands according to configuration
            if (b_v['att']['wave_nm'] < user_settings['dsf_wave_range'][0]):
                continue
            if (b_v['att']['wave_nm'] > user_settings['dsf_wave_range'][1]):
                continue

            print(band_slot, b_v['att']['rhot_ds'])

            band_data = b_v['data'] * 1.0
            band_shape = band_data.shape
            valid = np.isfinite(band_data) * (band_data > 0)
            mask = valid == False

            ## apply TOA filter
            if user_settings['dsf_filter_rhot']:
                print(f'Filtered {b_v["att"]["rhot_ds"]} using {user_settings["dsf_filter_percentile"]}th \
                         percentile in {user_settings["dsf_filter_box"][0]}x{user_settings["dsf_filter_box"][1]} pixel box')

                band_data[mask] = np.nanmedian(band_data)  ## fill mask with median
                # band_data = scipy.ndimage.median_filter(band_data, size=setu['dsf_filter_box'])
                band_data = scipy.ndimage.percentile_filter(band_data, user_settings['dsf_filter_percentile'],
                                                            size=user_settings['dsf_filter_box'])
                band_data[mask] = np.nan
            band_sub = np.where(valid)
            del valid, mask

            ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
            gk = ''

            ## fixed path reflectance
            if user_settings['dsf_aot_estimate'] == 'fixed':
                band_data_copy = band_data * 1.0
                if user_settings['dsf_spectrum_option'] == 'darkest':
                    band_data = np.array((np.nanpercentile(band_data[band_sub], 0)))
                if user_settings['dsf_spectrum_option'] == 'percentile':
                    band_data = np.array((np.nanpercentile(band_data[band_sub], user_settings['dsf_percentile'])))
                if user_settings['dsf_spectrum_option'] == 'intercept':
                    band_data = atmos.shared.intercept(band_data[band_sub], user_settings['dsf_intercept_pixels'])
                band_data.shape += (1, 1)  ## make 1,1 dimensions
                gk = '_mean'
                dark_pixel_location = np.where(band_data_copy <= band_data)
                if len(dark_pixel_location[0]) != 0:
                    dark_pixel_location_x = dark_pixel_location[0][0]
                    dark_pixel_location_y = dark_pixel_location[1][0]
                    print(dark_pixel_location_x, dark_pixel_location_y)
                    print(band_data)
                # if not use_revlut:
                #    gk='_mean'
                # else:
                #    band_data = np.tile(band_data, band_shape)
                print(band_slot, user_settings['dsf_spectrum_option'], f'{float(band_data[0, 0]):.3f}')

            ## tiled path reflectance
            elif user_settings['dsf_aot_estimate'] == 'tiled':
                gk = '_tiled'

                ## tile this band data
                tile_data = np.zeros((tiles[-1][0] + 1, tiles[-1][1] + 1), dtype=np.float32) + np.nan
                for t in range(len(tiles)):
                    ti, tj, subti, subtj = tiles[t]
                    tsub = band_data[subti[0]:subti[1], subtj[0]:subtj[1]]
                    tel = (subtj[1] - subtj[0]) * (subti[1] - subti[0])
                    nsub = len(np.where(np.isfinite(tsub))[0])
                    if nsub < tel * float(user_settings['dsf_min_tile_cover']):
                        continue

                    ## get per tile darkest
                    if user_settings['dsf_spectrum_option'] == 'darkest':
                        tile_data[ti, tj] = np.array((np.nanpercentile(tsub, 0)))
                    if user_settings['dsf_spectrum_option'] == 'percentile':
                        tile_data[ti, tj] = np.array((np.nanpercentile(tsub, user_settings['dsf_percentile'])))
                    if user_settings['dsf_spectrum_option'] == 'intercept':
                        tile_data[ti, tj] = atmos.shared.intercept(tsub, int(user_settings['dsf_intercept_pixels']))
                    del tsub

                ## fill nan tiles with closest values
                ind = scipy.ndimage.distance_transform_edt(np.isnan(tile_data), return_distances=False,
                                                           return_indices=True)
                band_data = tile_data[tuple(ind)]
                del tile_data, ind

            ## image is segmented based on input vector mask
            elif user_settings['dsf_aot_estimate'] == 'segmented':
                gk = '_segmented'
                if user_settings['dsf_spectrum_option'] == 'darkest':
                    band_data = np.array(
                        [np.nanpercentile(band_data[segment_data[segment]['sub']], 0)[0] for segment in
                         segment_data])
                if user_settings['dsf_spectrum_option'] == 'percentile':
                    band_data = np.array(
                        [np.nanpercentile(band_data[segment_data[segment]['sub']], user_settings['dsf_percentile'])[0]
                         for segment in segment_data])
                if user_settings['dsf_spectrum_option'] == 'intercept':
                    band_data = np.array([atmos.shared.intercept(band_data[segment_data[segment]['sub']],
                                                                 user_settings['dsf_intercept_pixels']) for segment in
                                          segment_data])
                band_data.shape += (1, 1)  ## make 2 dimensions
                # if verbosity > 2: print(b, setu['dsf_spectrum_option'], ['{:.3f}'.format(float(v)) for v in band_data])
            ## resolved per pixel dsf
            elif user_settings['dsf_aot_estimate'] == 'resolved':
                if not user_settings['resolved_geometry']:
                    gk = '_mean'
            else:
                print(f'DSF option {user_settings["dsf_aot_estimate"]} not configured')
                continue
            del band_sub

            ## do gas correction
            band_sub = np.where(np.isfinite(band_data))
            if len(band_sub[0]) > 0:
                band_data[band_sub] /= b_v['att']['tt_gas']

            ## store rhod
            if user_settings['dsf_aot_estimate'] in ['fixed', 'tiled', 'segmented']:
                dsf_rhod[band_slot] = band_data

            ## use band specific geometry if available
            gk_raa = f'{gk}'
            gk_vza = f'{gk}'
            if f'raa_{b_v["att"]["wave_name"]}' in l1r_datasets:
                gk_raa = f'_{b_v["att"]["wave_name"]}' + gk_raa
            if f'vza_{b_v["att"]["wave_name"]}' in l1r_datasets:
                gk_vza = f'_{b_v["att"]["wave_name"]}' + gk_vza

            ## compute aot
            aot_band = {}
            for l_i, lut_name in enumerate(luts):
                aot_band[lut_name] = np.zeros(band_data.shape, dtype=np.float32) + np.nan
                t0 = time.time()
                band_num = band_slot[1:]

                ## reverse lut interpolates rhot directly to aot
                if use_revlut:

                    if len(revl[lut_name]['rgi'][band_num].grid) == 5:
                        aot_band[lut_name][band_sub] = revl[lut_name]['rgi'][band_num](
                            (data_mem['pressure' + gk][band_sub],
                             data_mem['raa' + gk_raa][band_sub],
                             data_mem['vza' + gk_vza][band_sub],
                             data_mem['sza' + gk][band_sub],
                             band_data[band_sub]))
                    else:
                        aot_band[lut_name][band_sub] = revl[lut_name]['rgi'][band_num](
                            (data_mem['pressure' + gk][band_sub],
                             data_mem['raa' + gk_raa][band_sub],
                             data_mem['vza' + gk_vza][band_sub],
                             data_mem['sza' + gk][band_sub],
                             data_mem['wind' + gk][band_sub],
                             band_data[band_sub]))
                    # mask out of range aot
                    aot_band[lut_name][aot_band[lut_name] <= revl[lut_name]['minaot']] = np.nan
                    aot_band[lut_name][aot_band[lut_name] >= revl[lut_name]['maxaot']] = np.nan

                    ## replace nans with closest aot
                    if (user_settings['dsf_aot_fillnan']):
                        aot_band[lut_name] = atmos.shared.fillnan(aot_band[lut_name])

                ## standard lut interpolates rhot to results for different aot values
                else:
                    ## get rho path for lut steps in aot
                    if hyper:
                        # get modeled rhot for each wavelength
                        if rhot_aot is None:
                            ## set up array to store modeled rhot
                            rhot_aot = np.zeros((len(lutdw[lut_name]['meta']['tau']), \
                                                 len(lutdw[lut_name]['meta']['wave']), \
                                                 len(data_mem['pressure' + gk].flatten())))

                            ## compute rhot for range of aot
                            for ai, aot in enumerate(lutdw[lut_name]['meta']['tau']):
                                for pi in range(rhot_aot.shape[2]):
                                    tmp = lutdw[lut_name]['rgi']((data_mem['pressure' + gk].flatten()[pi],
                                                                  lutdw[lut_name]['ipd'][par],
                                                                  lutdw[lut_name]['meta']['wave'],
                                                                  data_mem['raa' + gk_raa].flatten()[pi],
                                                                  data_mem['vza' + gk_vza].flatten()[pi],
                                                                  data_mem['sza' + gk].flatten()[pi],
                                                                  data_mem['wind' + gk].flatten()[pi], aot))
                                    ## store current result
                                    rhot_aot[ai, :, pi] = tmp.flatten()
                            print('Shape of modeled rhot: {}'.format(rhot_aot.shape))
                        ## resample modeled results to current band
                        tmp = atmos.shared.rsr_convolute_nd(rhot_aot, lutdw[lut_name]['meta']['wave'],
                                                            rsrd['rsr'][band_num]['response'],
                                                            rsrd['rsr'][band_num]['wave'],
                                                            axis=1)

                        ## interpolate rho path to observation
                        aotret = np.zeros(aot_band[lut_name][band_sub].flatten().shape)
                        ## interpolate to observed rhot
                        for ri, crho in enumerate(band_data.flatten()):
                            aotret[ri] = np.interp(crho, tmp[:, ri], lutdw[lut_name]['meta']['tau'], left=left,
                                                   right=right)
                        print('Shape of computed aot: {}'.format(aotret.shape))
                        aot_band[lut_name][band_sub] = aotret.reshape(aot_band[lut_name][band_sub].shape)
                    else:
                        if len(data_mem['pressure' + gk]) > 1:
                            for gki in range(len(data_mem['pressure' + gk])):
                                tmp = lutdw[lut_name]['rgi'][band_num]((data_mem['pressure' + gk][gki],
                                                                        lutdw[lut_name]['ipd'][par],
                                                                        data_mem['raa' + gk_raa][gki],
                                                                        data_mem['vza' + gk_vza][gki],
                                                                        data_mem['sza' + gk][gki],
                                                                        data_mem['wind' + gk][gki],
                                                                        lutdw[lut_name]['meta']['tau']))
                                tmp = tmp.flatten()
                                aot_band[lut_name][gki] = np.interp(band_data[gki], tmp, lutdw[lut_name]['meta']['tau'],
                                                                    left=left, right=right)
                        else:
                            tmp = lutdw[lut_name]['rgi'][band_num]((data_mem['pressure' + gk],
                                                                    lutdw[lut_name]['ipd'][par],
                                                                    data_mem['raa' + gk_raa],
                                                                    data_mem['vza' + gk_vza],
                                                                    data_mem['sza' + gk],
                                                                    data_mem['wind' + gk],
                                                                    lutdw[lut_name]['meta']['tau']))
                            tmp = tmp.flatten()

                            ## interpolate rho path to observation
                            aot_band[lut_name][band_sub] = np.interp(band_data[band_sub], tmp,
                                                                     lutdw[lut_name]['meta']['tau'], left=left,
                                                                     right=right)

                ## mask minimum/maximum tile aots
                if user_settings['dsf_aot_estimate'] == 'tiled':
                    aot_band[lut_name][aot_band[lut_name] < user_settings['dsf_min_tile_aot']] = np.nan
                    aot_band[lut_name][aot_band[lut_name] > user_settings['dsf_max_tile_aot']] = np.nan

                tel = time.time() - t0
                print(
                    f'{global_attrs["sensor"]}/{band_slot} {lut_name} took {tel:.3f}s ({"RevLUT" if use_revlut else "StdLUT"})')

            ## store current band results
            aot_dict[band_slot] = aot_band
            aot_bands.append(band_slot)
            del band_data, band_sub, aot_band

        ## get min aot per pixel
        aot_stack = {}
        for l_i, lut_name in enumerate(luts):
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
            if user_settings['dsf_nbands'] < 2:
                user_settings['dsf_nbands'] = 2
            if user_settings['dsf_nbands'] > tmp.shape[2]:
                user_settings['dsf_nbands'] = tmp.shape[2]
            if user_settings['dsf_nbands_fit'] < 2:
                user_settings['dsf_nbands_fit'] = 2
            if user_settings['dsf_nbands_fit'] > tmp.shape[2]:
                user_settings['dsf_nbands_fit'] = tmp.shape[2]

            ## get minimum or average aot
            if user_settings['dsf_aot_compute'] in ['mean', 'median']:
                print(f'Using dsf_aot_compute = {user_settings["dsf_aot_compute"]}')
                ## stack n lowest bands
                for ai in range(user_settings['dsf_nbands']):
                    if ai == 0:
                        # find aot at 1st order
                        tmp_aot = aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, ai]] * 1.0
                    else:
                        # find aot at 2nd order
                        tmp_aot = np.dstack((tmp_aot, aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, ai]] * 1.0))
                ## compute mean over stack
                if user_settings['dsf_aot_compute'] == 'mean':
                    aot_stack[lut_name]['aot'] = np.nanmean(tmp_aot, axis=2)
                if user_settings['dsf_aot_compute'] == 'median':
                    aot_stack[lut_name]['aot'] = np.nanmedian(tmp_aot, axis=2)
                if user_settings['dsf_aot_estimate'] == 'fixed':
                    print(
                        f'Using dsf_aot_compute = {user_settings["dsf_aot_compute"]} {lut_name} aot = {float(aot_stack[lut_name]["aot"].flatten()):.3f}')
                tmp_aot = None
            else:
                aot_stack[lut_name]['aot'] = aot_stack[lut_name]['all'][
                    ax, ay, tmp[ax, ay, 0]]  # np.nanmin(aot_stack[lut]['all'], axis=2)

            ## if minimum for fixed retrieval is nan, set it to 0.01
            if user_settings['dsf_aot_estimate'] == 'fixed':
                if np.isnan(aot_stack[lut_name]['aot']):
                    aot_stack[lut_name]['aot'][0][0] = 0.01
            aot_stack[lut_name]['mask'] = ~np.isfinite(aot_stack[lut_name]['aot'])

            ## apply percentile filter
            if (user_settings['dsf_filter_aot']) & (user_settings['dsf_aot_estimate'] == 'resolved'):
                aot_stack[lut_name]['aot'] = scipy.ndimage.percentile_filter(aot_stack[lut_name]['aot'],
                                                                             user_settings['dsf_filter_percentile'],
                                                                             size=user_settings['dsf_filter_box'])
            ## apply gaussian kernel smoothing
            if (user_settings['dsf_smooth_aot']) & (user_settings['dsf_aot_estimate'] == 'resolved'):
                ## for gaussian smoothing of aot
                aot_stack[lut_name]['aot'] = scipy.ndimage.gaussian_filter(aot_stack[lut_name]['aot'],
                                                                           user_settings['dsf_smooth_box'], order=0,
                                                                           mode='nearest')

            ## mask aot
            aot_stack[lut_name]['aot'][aot_stack[lut_name]['mask']] = np.nan

            ## store bands for fitting rmsd
            for bbi in range(user_settings['dsf_nbands_fit']):
                aot_stack[lut_name][f'b{bbi + 1}'] = tmp[:, :, bbi].astype(int)  # .astype(float)
                aot_stack[lut_name][f'b{bbi + 1}'][aot_stack[lut_name]['mask']] = -1

            if user_settings['dsf_model_selection'] == 'min_dtau':
                ## array idices
                aid = np.indices(aot_stack[lut_name]['all'].shape[0:2])
                ## abs difference between first and second band tau
                aot_stack[lut_name]['dtau'] = np.abs(aot_stack[lut_name]['all'][aid[0, :], aid[1, :], tmp[:, :, 0]] - \
                                                     aot_stack[lut_name]['all'][aid[0, :], aid[1, :], tmp[:, :, 1]])
            ## remove sorted indices
            tmp = None
        ## select model based on min rmsd for 2 bands
        print(
            f'Choosing best fitting model: {user_settings["dsf_model_selection"]} ({user_settings["dsf_nbands"]} bands)')

        ## run through model results, get rhod and rhop for n lowest bands
        for l_i, lut_name in enumerate(luts):
            ## select model based on minimum rmsd between n best fitting bands
            if user_settings['dsf_model_selection'] == 'min_drmsd':

                print(f'Computing RMSD for model {lut_name}')

                rhop_f = np.zeros(
                    (aot_stack[lut_name]['b1'].shape[0], aot_stack[lut_name]['b1'].shape[1],
                     user_settings['dsf_nbands_fit']),
                    dtype=np.float32) + np.nan
                rhod_f = np.zeros(
                    (aot_stack[lut_name]['b1'].shape[0], aot_stack[lut_name]['b1'].shape[1],
                     user_settings['dsf_nbands_fit']),
                    dtype=np.float32) + np.nan

                for bi, band_slot in enumerate(aot_bands):
                    band_num = band_slot[1:]

                    ## use band specific geometry if available
                    gk_raa = gk
                    gk_vza = gk
                    if f'raa_{band_ds[band_slot]["att"]["wave_name"]}' in l1r_datasets:
                        gk_raa = f'_{band_ds[band_slot]["att"]["wave_name"]}' + gk_raa
                    if f'vza_{band_ds[band_slot]["att"]["wave_name"]}' in l1r_datasets:
                        gk_vza = f'_{band_ds[band_slot]["att"]["wave_name"]}' + gk_vza

                    ## run through two best fitting bands
                    fit_bands = [f'b{bbi + 1}' for bbi in range(user_settings['dsf_nbands_fit'])]
                    for ai, ab in enumerate(fit_bands):
                        aot_sub = np.where(aot_stack[lut_name][ab] == bi)
                        ## get rhod for current band
                        if (user_settings['dsf_aot_estimate'] == 'resolved'):
                            rhod_f[aot_sub[0], aot_sub[1], ai] = band_ds[band_slot]['data'][aot_sub]
                        elif (user_settings['dsf_aot_estimate'] == 'segmented'):
                            rhod_f[aot_sub[0], aot_sub[1], ai] = dsf_rhod[band_slot][aot_sub].flatten()
                        else:
                            rhod_f[aot_sub[0], aot_sub[1], ai] = dsf_rhod[band_slot][aot_sub]  # band_data / gas
                        ## get rho path for current band
                        if len(aot_sub[0]) > 0:
                            if (use_revlut):
                                xi = [data_mem['pressure' + gk][aot_sub],
                                      data_mem['raa' + gk_raa][aot_sub],
                                      data_mem['vza' + gk_vza][aot_sub],
                                      data_mem['sza' + gk][aot_sub],
                                      data_mem['wind' + gk][aot_sub]]
                            else:
                                xi = [data_mem['pressure' + gk],
                                      data_mem['raa' + gk_raa],
                                      data_mem['vza' + gk_vza],
                                      data_mem['sza' + gk],
                                      data_mem['wind' + gk]]
                            if hyper:
                                ## get hyperspectral results and resample to band
                                if len(aot_stack[lut_name]['aot'][aot_sub]) == 1:
                                    if len(xi[0]) == 0:
                                        res_hyp = lutdw[lut_name]['rgi'](
                                            (xi[0], lutdw[lut_name]['ipd'][par], lutdw[lut_name]['meta']['wave'],
                                             xi[1], xi[2], xi[3], xi[4], aot_stack[lut_name]['aot'][aot_sub]))
                                    else:  ## if more resolved geometry
                                        res_hyp = lutdw[lut_name]['rgi'](
                                            (xi[0][aot_sub], lutdw[lut_name]['ipd'][par],
                                             lutdw[lut_name]['meta']['wave'],
                                             xi[1][aot_sub], xi[2][aot_sub], xi[3][aot_sub], xi[4][aot_sub],
                                             aot_stack[lut_name]['aot'][aot_sub]))
                                    rhop_f[aot_sub[0], aot_sub[1], ai] = atmos.shared.rsr_convolute_nd(
                                        res_hyp.flatten(), lutdw[lut_name]['meta']['wave'],
                                        rsrd['rsr'][band_slot]['response'], rsrd['rsr'][band_slot]['wave'], axis=0)
                                else:
                                    for iii in range(len(aot_stack[lut_name]['aot'][aot_sub])):
                                        if len(xi[0]) == 0:
                                            res_hyp = lutdw[lut_name]['rgi'](
                                                (xi[0], lutdw[lut_name]['ipd'][par], lutdw[lut_name]['meta']['wave'],
                                                 xi[1], xi[2], xi[3], xi[4],
                                                 aot_stack[lut_name]['aot'][aot_sub][iii]))

                                        else:  ## if more resolved geometry
                                            res_hyp = lutdw[lut_name]['rgi']((xi[0].flatten()[iii],
                                                                              lutdw[lut_name]['ipd'][par],
                                                                              lutdw[lut_name]['meta']['wave'],
                                                                              xi[1].flatten()[iii],
                                                                              xi[2].flatten()[iii],
                                                                              xi[3].flatten()[iii],
                                                                              xi[4].flatten()[iii],
                                                                              aot_stack[lut_name]['aot'][aot_sub][iii]))
                                        rhop_f[
                                            aot_sub[0][iii], aot_sub[1][iii], ai] = atmos.shared.rsr_convolute_nd(
                                            res_hyp.flatten(), lutdw[lut_name]['meta']['wave'],
                                            rsrd['rsr'][band_slot]['response'], rsrd['rsr'][band_slot]['wave'], axis=0)
                            else:
                                if user_settings['dsf_aot_estimate'] == 'segmented':
                                    for gki in range(len(aot_sub[0])):
                                        rhop_f[aot_sub[0][gki], aot_sub[1][gki], ai] = lutdw[lut_name]['rgi'][
                                            band_slot](
                                            (xi[0][aot_sub[0][gki]], lutdw[lut_name]['ipd'][par],
                                             xi[1][aot_sub[0][gki]], xi[2][aot_sub[0][gki]],
                                             xi[3][aot_sub[0][gki]], xi[4][aot_sub[0][gki]],
                                             aot_stack[lut_name]['aot'][aot_sub][gki]))

                                else:
                                    rhop_f[aot_sub[0], aot_sub[1], ai] = lutdw[lut_name]['rgi'][band_num](
                                        (xi[0], lutdw[lut_name]['ipd'][par],
                                         xi[1], xi[2], xi[3], xi[4], aot_stack[lut_name]['aot'][aot_sub]))
                ## rmsd for current bands
                cur_sel_par = np.sqrt(
                    np.nanmean(np.square((rhod_f - rhop_f)), axis=2))  # band_data - lut value for aot to trans
                if (user_settings['dsf_aot_estimate'] == 'fixed'):
                    print(f'Computing RMSD for model {lut_name}: {cur_sel_par[0][0]:.4e}')

            ## end select with min RMSD

            ## select model based on minimum delta tau between two lowest aot bands
            if user_settings['dsf_model_selection'] == 'min_dtau':
                cur_sel_par = aot_stack[lut_name]['dtau']
            ## end select with min delta tau

            ## store minimum info
            if l_i == 0:
                aot_lut = np.zeros(aot_stack[lut_name]['aot'].shape, dtype=np.float32).astype(int)
                aot_lut[aot_stack[lut_name]['mask']] = -1
                aot_sel = aot_stack[lut_name]['aot'] * 1.0
                aot_sel_par = cur_sel_par * 1.0
                if user_settings['dsf_aot_estimate'] == 'fixed':
                    aot_sel_lut = '{}'.format(lut_name)
                    aot_sel_bands = [aot_stack[lut_name][f'{bb}'][0][0] for bb in fit_bands]
            else:
                aot_sub = np.where(cur_sel_par < aot_sel_par)
                if len(aot_sub[0]) == 0:
                    continue
                aot_lut[aot_sub] = l_i
                aot_sel[aot_sub] = aot_stack[lut_name]['aot'][aot_sub] * 1.0
                aot_sel_par[aot_sub] = cur_sel_par[aot_sub] * 1.0
                if user_settings['dsf_aot_estimate'] == 'fixed':
                    aot_sel_lut = f'{lut_name}'
                    aot_sel_bands = [aot_stack[lut_name][f'{bb}'][0][0] for bb in fit_bands]

        rhod_f = None
        rhod_p = None

    if (user_settings['dsf_aot_estimate'] == 'fixed') & (aot_sel_par is not None):
        print(f'Selected model {aot_sel_lut}: aot {aot_sel[0][0]:.3f}, RMSD {aot_sel_par[0][0]:.2e}')

    ## check variable aot, use most common LUT
    if (user_settings['dsf_aot_estimate'] != 'fixed') & (user_settings['dsf_aot_most_common_model']):
        print('Selecting most common model for processing.')
        n_aot = len(np.where(aot_lut != -1)[0])  # 0 = mod_1, 1 = mod2, -1 = null
        n_sel = 0
        for l_i, lut_name in enumerate(luts):
            sub = np.where(aot_lut == l_i)  # get indices where mod type is equal with current mod number
            n_cur = len(sub[0])
            if n_cur == 0:
                print(f'{lut_name}: {0:.1f}%')
            else:
                print(f'{lut_name}: {100 * n_cur / n_aot:.1f}%: mean aot of subset = {np.nanmean(aot_sel[sub]):.2f}')
            if n_cur >= n_sel:
                n_sel = n_cur
                li_sel = l_i
                aot_sel_lut = f'{lut_name}'
        ## set selected model
        aot_lut[:] = li_sel
        aot_sel[:] = aot_stack[aot_sel_lut]['aot'][:] * 1.0
        aot_sel_par[:] = np.nan  # to do
        print(f'Selected {aot_sel_lut}, mean aot = {np.nanmean(aot_sel):.2f}')
### end dark_spectrum_fitting