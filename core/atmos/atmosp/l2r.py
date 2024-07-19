import os, time, datetime
import numpy as np
import scipy.ndimage, scipy.interpolate
import skimage.measure
from core import atmos

def apply_l2r(l1r, gatts, settings=None):

    data_mem = {}
    l2r = {}
    rhos_to_band_name = {}
    l2r['bands'] = {}
    l2r['inputs'] = {}

    l2r_datasets = []

    if settings is not None:
        atmos.settings['user'] = atmos.setting.parse(None, settings=settings, merge=False)
        for k in atmos.settings['user']:
            atmos.settings['run'][k] = atmos.settings['user'][k]
    setu = atmos.setting.parse(gatts['sensor'], settings=atmos.settings['user'])
    for k in setu:
        atmos.settings['run'][k] = setu[k]

    if setu['dsf_exclude_bands'] != None:
        if type(setu['dsf_exclude_bands']) != list:
            setu['dsf_exclude_bands'] = [setu['dsf_exclude_bands']]
    else:
        setu['dsf_exclude_bands'] = []

    band_ds = l1r['bands'].copy()
    rhot_ds = [band_ds[key]['att']['rhot_ds'] for key in band_ds]
    rhot_bands = {
        rhot_name: band_ds[key]['data'] for key, rhot_name in zip(band_ds.keys(), rhot_ds)
    }
    l1r_datasets = list(l1r.keys())[:-1] + rhot_ds


    if setu['blackfill_skip']:
        rhot_wv = [int(band_ds[key]['att']['rhot_ds'].split('_')[-1]) for key in band_ds.keys()]  ## use last element of rhot name as wavelength
        bi, bw = atmos.shared.closest_idx(rhot_wv, setu['blackfill_wave'])
        closest_bkey = list(band_ds.keys())[bi]

        blackfill_target = 1.0 * band_ds[closest_bkey]['data']
        npx = blackfill_target.shape[0] * blackfill_target.shape[1]
        # nbf = npx - len(np.where(np.isfinite(band_data))[0])
        nbf = npx - len(np.where(np.isfinite(blackfill_target) * (blackfill_target > 0))[0])
        del blackfill_target
        if (nbf / npx) >= float(setu['blackfill_max']):
            print(f'Skipping scene as crop is {100 * nbf / npx:.0f}% blackfill')
            return ()

    print(f'Running acolite for {setu["inputfile"]}')

    dim_key = list(band_ds.keys())[-1]
    gatts['data_dimensions'] = band_ds[dim_key]['data'].shape
    gatts['data_elements'] = gatts['data_dimensions'][0] * gatts['data_dimensions'][1]

    rsrd = atmos.shared.rsr_dict(gatts['sensor'])

    hyper = False
    ## hyperspectral
    if gatts['sensor'] in atmos.config['hyper_sensors']:
        hyper = True
        rsr = atmos.shared.rsr_hyper(gatts['band_waves'], gatts['band_widths'], step=0.1)
        rsrd = atmos.shared.rsr_dict(rsrd={gatts['sensor']: {'rsr': rsr}})
        del rsr
    else:
        rsrd = atmos.shared.rsr_dict(gatts['sensor'])

    if gatts['sensor'] in rsrd:
        rsrd = rsrd[gatts['sensor']]
    else:
        print(f'Could not find {gatts["sensor"]} RSR')
        return()

    gatts['uoz'] = setu['uoz_default']
    gatts['uwv'] = setu['uwv_default']
    gatts['wind'] = setu['wind']
    gatts['pressure'] = setu['pressure']

    if (setu['ancillary_data']) & ((('lat' in l1r) & ('lon' in l1r)) | (('lat' in l1r) & ('lon' in l1r))):
        if ('lat' in l1r) & ('lon' in l1r):
            clon = np.nanmedian(l1r['lon'])
            clat = np.nanmedian(l1r['lat'])
        else:
            clon = gatts['lon']
            clat = gatts['lat']
        print(f'Getting ancillary data for {gatts["isodate"]} {clon:.3f}E {clat:.3f}N')
        anc = atmos.ac.ancillary.get(gatts['isodate'], clon, clat, verbosity=1)

        for k in ['uoz', 'uwv', 'wind', 'pressure']:
            if (k == 'pressure'):
                if (setu['pressure'] != setu['pressure_default']): continue
            if (k == 'wind') & (setu['wind'] is not None): continue
            if k in anc:
                gatts[k] = 1.0 * anc[k]

        del clon, clat, anc
    else:
        if (setu['s2_auxiliary_default']) & (gatts['sensor'][0:2] == 'S2') & (gatts['sensor'][4:] == 'MSI'):
            ## get mid point values from AUX ECMWFT
            if 'AUX_ECMWFT_msl_values' in gatts:
                gatts['pressure'] = gatts['AUX_ECMWFT_msl_values'][int(len(gatts['AUX_ECMWFT_msl_values'])/2)]/100 # convert from Pa to hPa
            if 'AUX_ECMWFT_tco3_values' in gatts:
                gatts['uoz'] = gatts['AUX_ECMWFT_tco3_values'][int(len(gatts['AUX_ECMWFT_tco3_values'])/2)] ** -1 * 0.0021415 # convert from kg/m2 to cm-atm
            if 'AUX_ECMWFT_tcwv_values' in gatts:
                gatts['uwv'] = gatts['AUX_ECMWFT_tcwv_values'][int(len(gatts['AUX_ECMWFT_tcwv_values'])/2)]/10 # convert from kg/m2 to g/cm2
            if 'AUX_ECMWFT__0u_values' in gatts and 'AUX_ECMWFT__0v_values' in gatts:  # S2Resampling, msiresampling
                u_wind = gatts['AUX_ECMWFT__0u_values'][int(len(gatts['AUX_ECMWFT__0u_values'])/2)]
                v_wind = gatts['AUX_ECMWFT__0v_values'][int(len(gatts['AUX_ECMWFT__0v_values'])/2)]
                gatts['wind'] = np.sqrt(u_wind * u_wind + v_wind * v_wind)

            ## interpolate to scene centre
            if setu['s2_auxiliary_interpolate']:
                if ('lat' in l1r_datasets) & ('lon' in l1r_datasets):
                    clon = np.nanmedian(l1r['lon'])
                    clat = np.nanmedian(l1r['lon'])
                else:
                    clon = gatts['lon']
                    clat = gatts['lat']
                ## pressure
                aux_par = 'ECMWFT_msl'
                if f'AUX_{aux_par}_values' in gatts:
                    lndi = scipy.interpolate.LinearNDInterpolator((gatts[f'AUX_{aux_par}_longitudes'],
                                                                   gatts[f'AUX_{aux_par}_latitudes']),
                                                                   gatts[f'AUX_{aux_par}_values'])
                    gatts['pressure'] = lndi(clon, clat)/100 # convert from Pa to hPa
                    del lndi
                elif 'msl' in l1r_datasets:  # S2Resampling, msiresampling
                    lndi = l1r['msl']
                    gatts['pressure'] = lndi(lndi.len/2, lndi.len/2) / 100  # convert from Pa to hPa
                    del lndi
                ## ozone
                aux_par = 'ECMWFT_tco3'
                if f'AUX_{aux_par}_values' in gatts:
                    lndi = scipy.interpolate.LinearNDInterpolator((gatts[f'AUX_{aux_par}_longitudes'],
                                                                   gatts[f'AUX_{aux_par}_latitudes']),
                                                                   gatts[f'AUX_{aux_par}_values'])
                    gatts['uoz'] = lndi(clon, clat)**-1 * 0.0021415 # convert from kg/m2 to cm-atm
                    del lndi
                ## water vapour
                aux_par = 'ECMWFT_tcwv'
                if f'AUX_{aux_par}_values' in gatts:
                    lndi = scipy.interpolate.LinearNDInterpolator((gatts[f'AUX_{aux_par}_longitudes'],
                                                                   gatts[f'AUX_{aux_par}_latitudes']),
                                                                   gatts[f'AUX_{aux_par}_values'])
                    gatts['uwv'] = lndi(clon, clat)/10 # convert from kg/m2 to g/cm2
                    del lndi
                elif 'tcwv' in l1r_datasets:
                    lndi = l1r['tcwv']
                    gatts['uwv'] = lndi(lndi.len/2, lndi.len/2) / 10  # convert from kg/m2 to g/cm2
                    del lndi
                del clon, clat

        ## elevation provided
    if setu['elevation'] is not None:
        setu['pressure'] = atmos.ac.pressure_elevation(setu['elevation'])
        gatts['pressure'] = setu['pressure']
        print(gatts['pressure'])

    ## dem pressure
    if setu['dem_pressure']:
        print(f'Extracting {setu["dem_source"]} DEM data')
        if ('lat' in l1r_datasets) & ('lon' in l1r_datasets):
            dem = atmos.dem.dem_lonlat(l1r['lon'], l1r['lat'], source=setu['dem_source'])
        else:
            dem = atmos.dem.dem_lonlat(gatts['lon'], gatts['lon'], source=setu['dem_source'])

        if dem is not None:
            dem_pressure = atmos.ac.pressure_elevation(dem)

            if setu['dem_pressure_resolved']:
                l1r['data_mem']['pressure'] = dem_pressure
                gatts['pressure'] = np.nanmean(l1r['data_mem']['pressure'])
            else:
                l1r['data_mem']['pressure'] = np.nanpercentile(dem_pressure, setu['dem_pressure_percentile'])
                gatts['pressure'] = l1r['data_mem']['pressure']
            l1r_datasets.append('pressure')

            if setu['dem_pressure_write']:
                l1r['data_mem']['dem'] = dem.astype(np.float32)
                l1r['data_mem']['dem_pressure'] = dem_pressure
        else:
            print('Could not determine elevation from {} DEM data'.format(setu['dem_source']))

        dem = None
        dem_pressure = None

    print(f'default uoz: {setu["uoz_default"]:.2f} uwv: {setu["uwv_default"]:.2f} pressure: {setu["pressure_default"]:.2f}')
    print(f'current uoz: {gatts["uoz"]:.2f} uwv: {gatts["uwv"]:.2f} pressure: {gatts["pressure"]:.2f}')

    ## which LUT data to read
    if (setu['dsf_interface_reflectance']):
        if (setu['dsf_interface_option'] == 'default'):
            par = 'romix+rsky_t'
        elif (setu['dsf_interface_option'] == '6sv'):
            par = 'romix+rsurf'
            print(par)
    else:
        par = 'romix'

    ## set wind to wind range
    if gatts['wind'] is None: gatts['wind'] = setu['wind_default']
    if par == 'romix+rsurf':
        gatts['wind'] = max(2, gatts['wind'])
        gatts['wind'] = min(20, gatts['wind'])
    else:
        gatts['wind'] = max(0.1, gatts['wind'])
        gatts['wind'] = min(20, gatts['wind'])

    ## get mean average geometry
    geom_ds = ['sza', 'vza', 'raa', 'pressure', 'wind']
    for ds in l1r_datasets:
        if ('raa_' in l1r_datasets) or ('vza_' in ds):
            geom_ds.append(ds)

    if 'sza' in l1r_datasets:
        sza = l1r['sza']
        high_sza = np.where(sza > setu['sza_limit'])
        if len(high_sza[0]) > 0:
            print('Warning: SZA out of LUT range')
            print(f'Mean SZA: {np.nanmean(sza):.3f}')
            if (setu['sza_limit_replace']):
                sza[high_sza] = setu['sza_limit']
                print(f'Mean SZA after replacing SZA > {setu["sza_limit"]}: {np.nanmean(sza):.3f}')
        del sza, high_sza

    geom_mean = {k: np.nanmean(l1r[k]) if k in l1r_datasets else gatts[k] for k in geom_ds}

    if (geom_mean['sza'] > setu['sza_limit']):
        print('Warning: SZA out of LUT range')
        print(f'Mean SZA: {geom_mean["sza"]:.3f}')
        if (setu['sza_limit_replace']):
            geom_mean['sza'] = setu['sza_limit']
            print(f'Mean SZA after replacing SZA > {setu["sza_limit"]}: {geom_mean["sza"]:.3f}')

    if (geom_mean['vza'] > setu['vza_limit']):
        print('Warning: VZA out of LUT range')
        print(f'Mean VZA: {geom_mean["vza"]:.3f}')
        if (setu['vza_limit_replace']):
            geom_mean['vza'] = setu['vza_limit']
            print(f'Mean VZA after replacing VZA > {setu["vza_limit"]}: {geom_mean["vza"]:.3f}')

    ## get gas transmittance
    tg_dict = atmos.ac.gas_transmittance(geom_mean['sza'], geom_mean['vza'],
                                      uoz=gatts['uoz'], uwv=gatts['uwv'],
                                      rsr=rsrd['rsr'])

    ## make bands dataset
    for bi, b_k in enumerate(rsrd['rsr_bands']):
        band_key = f'B{b_k}'
        if band_key in band_ds:
            for k in ['wave_mu', 'wave_nm', 'wave_name']:
                if b_k in rsrd[k]:
                    band_ds[band_key]['att'][k] = rsrd[k][b_k]

            band_ds[band_key]['att']['rhot_ds'] = f'rhot_{band_ds[band_key]["att"]["wave_name"]}'
            band_ds[band_key]['att']['rhos_ds'] = f'rhos_{band_ds[band_key]["att"]["wave_name"]}'

            if setu['add_band_name']:
                band_ds[band_key]["att"]['rhot_ds'] = f'rhot_{b_k}_{band_ds[band_key]["att"]["wave_name"]}'
                band_ds[band_key]["att"]['rhos_ds'] = f'rhos_{b_k}_{band_ds[band_key]["att"]["wave_name"]}'
            if setu['add_detector_name']:
                dsname = rhot_ds[bi][5:]
                band_ds[band_key]["att"]['rhot_ds'] = f'rhot_{dsname}'
                band_ds[band_key]["att"]['rhos_ds'] = f'rhos_{dsname}'

            for k in tg_dict:
                if k not in ['wave']:
                    band_ds[band_key]['att'][k] = tg_dict[k][b_k]
                    if setu['gas_transmittance'] is False:
                        band_ds[band_key]['att'][k] = 1.0
            band_ds[band_key]['att']['wavelength'] = band_ds[band_key]['att']['wave_nm']
    ## end bands dataset
    del band_ds, tg_dict

    ## atmospheric correction
    if setu['aerosol_correction'] == 'dark_spectrum':
        ac_opt = 'dsf'
    elif setu['aerosol_correction'] == 'exponential':
        ac_opt = 'exp'
    else:
        print(f'Option aerosol_correction {setu["aerosol_correction"]} not configured')
        ac_opt = 'dsf'
    print(f'Using {ac_opt.upper()} atmospheric correction')

    if setu['resolved_geometry'] & hyper:
        print('Resolved geometry for hyperspectral sensors currently not supported')
        setu['resolved_geometry'] = False

    use_revlut = False
    per_pixel_geometry = False

    ## if path reflectance is tiled or resolved, use reverse lut
    ## no need to use reverse lut if fixed geometry is used
    ## we want to use the reverse lut to derive aot if the geometry data is resolved
    for ds in geom_ds:
        if ds not in l1r_datasets:
            data_mem[ds] = geom_mean[ds]
        else:
            data_mem[ds] = l1r[ds]

        if len(np.atleast_1d(data_mem[ds]))>1:
            use_revlut=True ## if any dataset more than 1 dimension use revlut
            per_pixel_geometry = True
        else: ## convert floats into arrays
            data_mem[ds] = np.asarray(data_mem[ds])
            data_mem[ds].shape+=(1,1)
        data_mem[f'{ds}_mean'] = np.asarray(np.nanmean(data_mem[ds])) ## also store tile mean
        data_mem[f'{ds}_mean'].shape+=(1,1) ## make 1,1 dimensions

    del geom_mean

    ## for tiled processing track tile positions and average geometry
    tiles = []
    if 'dsf_tile_dimensions' not in setu: setu['dsf_tile_dimensions'] = None
    if (setu['dsf_aot_estimate'] == 'tiled') & (setu['dsf_tile_dimensions'] is not None):
        ni = np.ceil(gatts['data_dimensions'][0]/setu['dsf_tile_dimensions'][0]).astype(int)
        nj = np.ceil(gatts['data_dimensions'][1]/setu['dsf_tile_dimensions'][1]).astype(int)
        if (ni <= 1) | (nj <= 1):
            print(f'Scene too small for tiling ({ni}x{nj} tiles of {setu["dsf_tile_dimensions"][0]}x{setu["dsf_tile_dimensions"][1]} pixels), using fixed processing')
            setu['dsf_aot_estimate'] = 'fixed'
        else:
            ntiles = ni*nj
            print('Processing with {} tiles ({}x{} tiles of {}x{} pixels)'.format(ntiles, ni, nj, setu['dsf_tile_dimensions'][0], setu['dsf_tile_dimensions'][1]))

            ## compute tile dimensions
            for ti in range(ni):
                for tj in range(nj):
                    subti = [setu['dsf_tile_dimensions'][0]*ti, setu['dsf_tile_dimensions'][0]*(ti+1)]
                    subti[1] = np.min((subti[1], gatts['data_dimensions'][0]))
                    subtj = [setu['dsf_tile_dimensions'][1]*tj, setu['dsf_tile_dimensions'][1]*(tj+1)]
                    subtj[1] = np.min((subtj[1], gatts['data_dimensions'][1]))
                    tiles.append((ti, tj, subti, subtj))

            ## create tile geometry datasets
            for ds in geom_ds:
                if len(np.atleast_1d(data_mem[ds]))>1: ## if not fixed geometry
                    data_mem[f'{ds}_tiled'] = np.zeros((ni,nj), dtype=np.float32)+np.nan
                    for t in range(ntiles):
                        ti, tj, subti, subtj = tiles[t]
                        data_mem[f'{ds}_tiled'][ti, tj] = \
                            np.nanmean(data_mem[ds][subti[0]:subti[1],subtj[0]:subtj[1]])
                else: ## if fixed geometry
                    if per_pixel_geometry:
                        data_mem[f'{ds}_tiled'] = np.zeros((ni,nj), dtype=np.float32)+data_mem[ds]
                    else:
                        data_mem[f'{ds}_tiled'] = 1.0 * data_mem[ds]

            ## remove full geom datasets as tiled will be used
            for ds in geom_ds:
                if f'{ds}_tiled' in data_mem:
                    del data_mem[ds]
    ## end tiling

    ## set up image segments
    if setu['dsf_aot_estimate'] == 'segmented':
        segment_data = {}
        first_key = list(rhot_bands.keys())[0]
        finite_mask = np.isfinite(rhot_bands[first_key])
        segment_mask = skimage.measure.label(finite_mask)
        segments = np.unique(segment_mask)

        ## find and label segments
        for segment in segments:
            #if segment == 0: continue
            seg_sub = np.where((segment_mask == segment) & (finite_mask))
            #if len(seg_sub[0]) == 0: continue
            if len(seg_sub[0]) < max(1, setu['dsf_minimum_segment_size']):
                print('Skipping segment of {} pixels'.format(len(seg_sub[0])))
                continue
            segment_data[segment] = {'segment': segment, 'sub': seg_sub}

        if len(segment_data) <= 1:
            print('Image segmentation only found {} segments'.format(len(segment_data)))
            print('Proceeding with dsf_aot_estimate=fixed')
            setu['dsf_aot_estimate'] = 'fixed'
        else:
            if setu['verbosity'] > 3:
                print(f'Found {len(segment_data)} segments')
            for segment in segment_data:
                if setu['verbosity'] > 4:
                    print(f'Segment {segment}/{len(segment_data)}: {len(segment_data[segment]["sub"][0])} pixels')
            ## convert geometry and ancillary data
            for ds in geom_ds:
                if len(np.atleast_1d(data_mem[ds]))>1: ## if not fixed geometry
                    data_mem['{}_segmented'.format(ds)] = [np.nanmean(data_mem[ds][segment_data[segment]['sub']]) for segment in segment_data]
                else:
                    data_mem['{}_segmented'.format(ds)] = [1.0 * data_mem[ds] for segment in segment_data]
                data_mem['{}_segmented'.format(ds)] = np.asarray(data_mem['{}_segmented'.format(ds)]).flatten()
    ## end segmenting

    if (not setu['resolved_geometry']) & (setu['dsf_aot_estimate'] != 'tiled'):
        use_revlut = False
    if setu['dsf_aot_estimate'] in ['fixed', 'segmented']:
        use_revlut = False
    if hyper:
        use_revlut = False

    ## set LUT dimension parameters to correct shape if resolved processing
    if (use_revlut) & (per_pixel_geometry) & (setu['dsf_aot_estimate'] == 'resolved'):
        for ds in geom_ds:
            if len(np.atleast_1d(data_mem[ds]))!=1:
                continue
            print(f'Reshaping {ds} to {gatts["data_dimensions"][0]}x{gatts["data_dimensions"][1]} pixels for resolved processing')
            data_mem[ds] = np.repeat(data_mem[ds], gatts['data_elements']).reshape(gatts['data_dimensions'])

    ## do not allow LUT boundaries ()
    left, right = np.nan, np.nan
    if setu['dsf_allow_lut_boundaries']:
        left, right = None, None

    ## setup output file
    # ofile = None
    # if output_file:
    #     if target_file is None:
    #         ofile = setu["inputfile"].replace('_L1R', '_L2R')
    #         # if ('output' in setu) & (output is None): output = setu['output']
    #         if output is None: output = output_
    #         ofile = '{}/{}'.format(output, os.path.basename(ofile))
    #     else:
    #         ofile = '{}'.format(target_file)
    #
    #     gemo = ac.gem.gem(ofile, new=True)
    #     gemo.gatts = {k: gatts[k] for k in gatts}
    #     gemo.nc_projection = gem.nc_projection
    #     gemo.gatts['acolite_file_type'] = 'L2R'
    #     gemo.gatts['ofile'] = ofile
    #
    #     gemo.bands = gem.bands
    #     gemo.verbosity = setu['verbosity']
    #     gemo.gatts['acolite_version'] = ac.version
    #
    #     ## add settings to gatts
    #     for k in setu:
    #         if k in gatts: continue
    #         if setu[k] in [True, False]:
    #             gemo.gatts[k] = str(setu[k])
    #         else:
    #             gemo.gatts[k] = setu[k]
    #
    #     ## copy datasets from inputfile
    #     copy_rhot = False
    #     copy_datasets = []
    #     if setu['copy_datasets'] is not None: copy_datasets += setu['copy_datasets']
    #     if setu['output_bt']: copy_datasets += [ds for ds in datasets if ds[0:2] == 'bt']
    #     if setu['output_xy']: copy_datasets += ['x', 'y']
    #
    #     if len(copy_datasets) > 0:
    #         ## copy rhot all from L1R
    #         if 'rhot_*' in copy_datasets:
    #             copy_datasets.remove('rhot_*')
    #             copy_rhot = True
    #         ## copy datasets to L2R
    #         for ds in copy_datasets:
    #             if (ds not in datasets):
    #                 if verbosity > 2: print('{} not found in {}'.format(ds, setu["inputfile"]))
    #                 continue
    #             if verbosity > 1: print('Writing {}'.format(ds))
    #             cdata, catts = gem.data(ds, attributes=True)
    #             gemo.write(ds, cdata, ds_att=catts)
    #             del cdata, catts
    #
    #     ## write dem
    #     if setu['dem_pressure_write']:
    #         for k in ['dem', 'dem_pressure']:
    #             if k in gem.data_mem:
    #                 gemo.write(k, gem.data_mem[k])
    #                 gem.data_mem[k] = None

    t0 = time.time()
    print(f'Loading LUTs {setu["luts"]}')
    ## load reverse lut romix -> aot
    if use_revlut:
        revl = atmos.aerlut.reverse_lut(gatts['sensor'], par=par, rsky_lut=setu['dsf_interface_lut'], base_luts=setu['luts'])

    ## load aot -> atmospheric parameters lut
    ## QV 2022-04-04 interface reflectance is always loaded since we include wind in the interpolation below
    ## not necessary for runs with par == romix, to be fixed
    lutdw = atmos.aerlut.import_luts(add_rsky=True, par=(par if par == 'romix+rsurf' else 'romix+rsky_t'),
                                  sensor=None if hyper else gatts['sensor'],
                                  rsky_lut=setu['dsf_interface_lut'],
                                  base_luts=setu['luts'], pressures=setu['luts_pressures'],
                                  reduce_dimensions=setu['luts_reduce_dimensions'])
    luts = list(lutdw.keys())
    print(f'Loading LUTs took {(time.time() - t0):.1f} s')

    ## #####################
    ## dark spectrum fitting
    aot_lut = None
    aot_sel= None
    aot_sel_lut = None
    aot_sel_par = None

    if (ac_opt == 'dsf'):
        ## user supplied aot
        if (setu['dsf_fixed_aot'] is not None):
            setu['dsf_aot_estimate'] = 'fixed'
            aot_lut = None
            for l_i, lut_name in enumerate(luts):
                if lut_name == setu['dsf_fixed_lut']:
                    aot_lut = np.array(l_i)
                    aot_lut.shape += (1, 1)  ## make 1,1 dimensions
            if aot_lut is None:
                print(f'LUT {setu["dsf_fixed_lut"]} not recognised')

            aot_sel = np.array(float(setu['dsf_fixed_aot']))
            aot_sel.shape += (1, 1)  ## make 1,1 dimensions
            aot_sel_lut = luts[aot_lut[0][0]]
            aot_sel_par = None
            print(f'User specified aot {aot_sel[0][0]} and model {aot_sel_lut}')

            ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
            gk = '' if use_revlut else '_mean'
        ## image derived aot
        else:
            if setu['dsf_spectrum_option'] not in ['darkest', 'percentile', 'intercept']:
                print('dsf_spectrum_option {} not configured, falling back to darkest'.format(
                    setu['dsf_spectrum_option']))
                setu['dsf_spectrum_option'] = 'darkest'

            rhot_aot = None
            ## run through bands to get aot
            aot_bands = []
            aot_dict = {}
            dsf_rhod = {}
            band_ds = l1r['bands']
            for bi, (b_k, b_v) in enumerate(band_ds.items()):
                if (b_k in setu['dsf_exclude_bands']):
                    continue
                if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
                    continue
                if b_v['att']['rhot_ds'] not in l1r_datasets:
                    continue

                ## skip band for aot computation
                if b_v['att']['tt_gas'] < setu['min_tgas_aot']:
                    continue

                ## skip bands according to configuration
                if (b_v['att']['wave_nm'] < setu['dsf_wave_range'][0]):
                    continue
                if (b_v['att']['wave_nm'] > setu['dsf_wave_range'][1]):
                    continue

                print(b_k, b_v['att']['rhot_ds'])

                band_data = b_v['data'] * 1.0
                band_shape = band_data.shape
                valid = np.isfinite(band_data) * (band_data > 0)
                mask = valid == False

                ## apply TOA filter
                if setu['dsf_filter_rhot']:
                    print(f'Filtered {b_v["att"]["rhot_ds"]} using {setu["dsf_filter_percentile"]}th \
                     percentile in {setu["dsf_filter_box"][0]}x{setu["dsf_filter_box"][1]} pixel box')

                    band_data[mask] = np.nanmedian(band_data)  ## fill mask with median
                    # band_data = scipy.ndimage.median_filter(band_data, size=setu['dsf_filter_box'])
                    band_data = scipy.ndimage.percentile_filter(band_data, setu['dsf_filter_percentile'],
                                                                size=setu['dsf_filter_box'])
                    band_data[mask] = np.nan
                band_sub = np.where(valid)
                del valid, mask

                ## geometry key '' if using resolved, otherwise '_mean' or '_tiled'
                gk = ''

                ## fixed path reflectance
                if setu['dsf_aot_estimate'] == 'fixed':
                    band_data_copy = band_data * 1.0
                    if setu['dsf_spectrum_option'] == 'darkest':
                        band_data = np.array((np.nanpercentile(band_data[band_sub], 0)))
                    if setu['dsf_spectrum_option'] == 'percentile':
                        band_data = np.array((np.nanpercentile(band_data[band_sub], setu['dsf_percentile'])))
                    if setu['dsf_spectrum_option'] == 'intercept':
                        band_data = atmos.shared.intercept(band_data[band_sub], setu['dsf_intercept_pixels'])
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
                    print(b_k, setu['dsf_spectrum_option'], f'{float(band_data[0, 0]):.3f}')

                ## tiled path reflectance
                elif setu['dsf_aot_estimate'] == 'tiled':
                    gk = '_tiled'

                    ## tile this band data
                    tile_data = np.zeros((tiles[-1][0] + 1, tiles[-1][1] + 1), dtype=np.float32) + np.nan
                    for t in range(len(tiles)):
                        ti, tj, subti, subtj = tiles[t]
                        tsub = band_data[subti[0]:subti[1], subtj[0]:subtj[1]]
                        tel = (subtj[1] - subtj[0]) * (subti[1] - subti[0])
                        nsub = len(np.where(np.isfinite(tsub))[0])
                        if nsub < tel * float(setu['dsf_min_tile_cover']):
                            continue

                        ## get per tile darkest
                        if setu['dsf_spectrum_option'] == 'darkest':
                            tile_data[ti, tj] = np.array((np.nanpercentile(tsub, 0)))
                        if setu['dsf_spectrum_option'] == 'percentile':
                            tile_data[ti, tj] = np.array((np.nanpercentile(tsub, setu['dsf_percentile'])))
                        if setu['dsf_spectrum_option'] == 'intercept':
                            tile_data[ti, tj] = atmos.shared.intercept(tsub, int(setu['dsf_intercept_pixels']))
                        del tsub

                    ## fill nan tiles with closest values
                    ind = scipy.ndimage.distance_transform_edt(np.isnan(tile_data), return_distances=False,
                                                               return_indices=True)
                    band_data = tile_data[tuple(ind)]
                    del tile_data, ind

                ## image is segmented based on input vector mask
                elif setu['dsf_aot_estimate'] == 'segmented':
                    gk = '_segmented'
                    if setu['dsf_spectrum_option'] == 'darkest':
                        band_data = np.array(
                            [np.nanpercentile(band_data[segment_data[segment]['sub']], 0)[0] for segment in
                             segment_data])
                    if setu['dsf_spectrum_option'] == 'percentile':
                        band_data = np.array(
                            [np.nanpercentile(band_data[segment_data[segment]['sub']], setu['dsf_percentile'])[0]
                             for segment in segment_data])
                    if setu['dsf_spectrum_option'] == 'intercept':
                        band_data = np.array([atmos.shared.intercept(band_data[segment_data[segment]['sub']],
                                                                  setu['dsf_intercept_pixels']) for segment in
                                              segment_data])
                    band_data.shape += (1, 1)  ## make 2 dimensions
                    # if verbosity > 2: print(b, setu['dsf_spectrum_option'], ['{:.3f}'.format(float(v)) for v in band_data])
                ## resolved per pixel dsf
                elif setu['dsf_aot_estimate'] == 'resolved':
                    if not setu['resolved_geometry']:
                        gk = '_mean'
                else:
                    print(f'DSF option {setu["dsf_aot_estimate"]} not configured')
                    continue
                del band_sub

                ## do gas correction
                band_sub = np.where(np.isfinite(band_data))
                if len(band_sub[0]) > 0:
                    band_data[band_sub] /= b_v['att']['tt_gas']

                ## store rhod
                if setu['dsf_aot_estimate'] in ['fixed', 'tiled', 'segmented']:
                    dsf_rhod[b_k] = band_data

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
                    band_num = b_k[1:]

                    ## reverse lut interpolates rhot directly to aot
                    if use_revlut:

                        if len(revl[lut_name]['rgi'][band_num].grid) == 5:
                            aot_band[lut_name][band_sub] = revl[lut_name]['rgi'][band_num]((data_mem['pressure' + gk][band_sub],
                                                                           data_mem['raa' + gk_raa][band_sub],
                                                                           data_mem['vza' + gk_vza][band_sub],
                                                                           data_mem['sza' + gk][band_sub],
                                                                           band_data[band_sub]))
                        else:
                            aot_band[lut_name][band_sub] = revl[lut_name]['rgi'][band_num]((data_mem['pressure' + gk][band_sub],
                                                                           data_mem['raa' + gk_raa][band_sub],
                                                                           data_mem['vza' + gk_vza][band_sub],
                                                                           data_mem['sza' + gk][band_sub],
                                                                           data_mem['wind' + gk][band_sub],
                                                                           band_data[band_sub]))
                        # mask out of range aot
                        aot_band[lut_name][aot_band[lut_name] <= revl[lut_name]['minaot']] = np.nan
                        aot_band[lut_name][aot_band[lut_name] >= revl[lut_name]['maxaot']] = np.nan

                        ## replace nans with closest aot
                        if (setu['dsf_aot_fillnan']):
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
                                                             rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'],
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
                                                            data_mem['wind' + gk], lutdw[lut_name]['meta']['tau']))
                                tmp = tmp.flatten()

                                ## interpolate rho path to observation
                                aot_band[lut_name][band_sub] = np.interp(band_data[band_sub], tmp,
                                                                    lutdw[lut_name]['meta']['tau'], left=left,
                                                                    right=right)

                    ## mask minimum/maximum tile aots
                    if setu['dsf_aot_estimate'] == 'tiled':
                        aot_band[lut_name][aot_band[lut_name] < setu['dsf_min_tile_aot']] = np.nan
                        aot_band[lut_name][aot_band[lut_name] > setu['dsf_max_tile_aot']] = np.nan

                    tel = time.time() - t0
                    print(f'{gatts["sensor"]}/{b_k} {lut_name} took {tel:.3f}s ({"RevLUT" if use_revlut else "StdLUT"})')

                ## store current band results
                aot_dict[b_k] = aot_band
                aot_bands.append(b_k)
                del band_data, band_sub, aot_band

            ## get min aot per pixel
            aot_stack = {}
            for l_i, lut_name in enumerate(luts):
                aot_band_list = []
                ## stack aot for this lut
                for bi, b_k in enumerate(aot_bands):
                    if b_k not in aot_dict:
                        continue
                    aot_band_list.append(b_k)
                    if lut_name not in aot_stack:
                        aot_stack[lut_name] = {'all': aot_dict[b_k][lut_name] * 1.0}
                    else:
                        aot_stack[lut_name]['all'] = np.dstack((aot_stack[lut_name]['all'],
                                                           aot_dict[b_k][lut_name]))
                aot_stack[lut_name]['band_list'] = aot_band_list

                ## get highest aot per pixel for all bands
                tmp = np.argsort(aot_stack[lut_name]['all'], axis=2)
                ay, ax = np.meshgrid(np.arange(tmp.shape[1]), np.arange(tmp.shape[0]))

                ## identify number of bands
                if setu['dsf_nbands'] < 2:
                    setu['dsf_nbands'] = 2
                if setu['dsf_nbands'] > tmp.shape[2]:
                    setu['dsf_nbands'] = tmp.shape[2]
                if setu['dsf_nbands_fit'] < 2:
                    setu['dsf_nbands_fit'] = 2
                if setu['dsf_nbands_fit'] > tmp.shape[2]:
                    setu['dsf_nbands_fit'] = tmp.shape[2]

                ## get minimum or average aot
                if setu['dsf_aot_compute'] in ['mean', 'median']:
                    print(f'Using dsf_aot_compute = {setu["dsf_aot_compute"]}')
                    ## stack n lowest bands
                    for ai in range(setu['dsf_nbands']):
                        if ai == 0:
                            # find aot at 1st order
                            tmp_aot = aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, ai]] * 1.0
                        else:
                            # find aot at 2nd order
                            tmp_aot = np.dstack((tmp_aot, aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, ai]] * 1.0))
                    ## compute mean over stack
                    if setu['dsf_aot_compute'] == 'mean':
                        aot_stack[lut_name]['aot'] = np.nanmean(tmp_aot, axis=2)
                    if setu['dsf_aot_compute'] == 'median':
                        aot_stack[lut_name]['aot'] = np.nanmedian(tmp_aot, axis=2)
                    if setu['dsf_aot_estimate'] == 'fixed':
                        print(f'Using dsf_aot_compute = {setu["dsf_aot_compute"]} {lut_name} aot = {float(aot_stack[lut_name]["aot"].flatten()):.3f}')
                    tmp_aot = None
                else:
                    aot_stack[lut_name]['aot'] = aot_stack[lut_name]['all'][ax, ay, tmp[ax, ay, 0]]  # np.nanmin(aot_stack[lut]['all'], axis=2)

                ## if minimum for fixed retrieval is nan, set it to 0.01
                if setu['dsf_aot_estimate'] == 'fixed':
                    if np.isnan(aot_stack[lut_name]['aot']):
                        aot_stack[lut_name]['aot'][0][0] = 0.01
                aot_stack[lut_name]['mask'] = ~np.isfinite(aot_stack[lut_name]['aot'])

                ## apply percentile filter
                if (setu['dsf_filter_aot']) & (setu['dsf_aot_estimate'] == 'resolved'):
                    aot_stack[lut_name]['aot'] = scipy.ndimage.percentile_filter(aot_stack[lut_name]['aot'],
                                                                                 setu['dsf_filter_percentile'],
                                                                                 size=setu['dsf_filter_box'])
                ## apply gaussian kernel smoothing
                if (setu['dsf_smooth_aot']) & (setu['dsf_aot_estimate'] == 'resolved'):
                    ## for gaussian smoothing of aot
                    aot_stack[lut_name]['aot'] = scipy.ndimage.gaussian_filter(aot_stack[lut_name]['aot'],
                                                                          setu['dsf_smooth_box'], order=0,
                                                                          mode='nearest')

                ## mask aot
                aot_stack[lut_name]['aot'][aot_stack[lut_name]['mask']] = np.nan

                ## store bands for fitting rmsd
                for bbi in range(setu['dsf_nbands_fit']):
                    aot_stack[lut_name][f'b{bbi + 1}'] = tmp[:, :, bbi].astype(int)  # .astype(float)
                    aot_stack[lut_name][f'b{bbi + 1}'][aot_stack[lut_name]['mask']] = -1

                if setu['dsf_model_selection'] == 'min_dtau':
                    ## array idices
                    aid = np.indices(aot_stack[lut_name]['all'].shape[0:2])
                    ## abs difference between first and second band tau
                    aot_stack[lut_name]['dtau'] = np.abs(aot_stack[lut_name]['all'][aid[0, :], aid[1, :], tmp[:, :, 0]] - \
                                                    aot_stack[lut_name]['all'][aid[0, :], aid[1, :], tmp[:, :, 1]])
                ## remove sorted indices
                tmp = None
            ## select model based on min rmsd for 2 bands
            print(f'Choosing best fitting model: {setu["dsf_model_selection"]} ({setu["dsf_nbands"]} bands)')

            ## run through model results, get rhod and rhop for n lowest bands
            for l_i, lut_name in enumerate(luts):
                ## select model based on minimum rmsd between n best fitting bands
                if setu['dsf_model_selection'] == 'min_drmsd':

                    print(f'Computing RMSD for model {lut_name}')

                    rhop_f = np.zeros(
                        (aot_stack[lut_name]['b1'].shape[0], aot_stack[lut_name]['b1'].shape[1], setu['dsf_nbands_fit']),
                        dtype=np.float32) + np.nan
                    rhod_f = np.zeros(
                        (aot_stack[lut_name]['b1'].shape[0], aot_stack[lut_name]['b1'].shape[1], setu['dsf_nbands_fit']),
                        dtype=np.float32) + np.nan

                    for bi, b_k in enumerate(aot_bands):
                        band_num = b_k[1:]

                        ## use band specific geometry if available
                        gk_raa = gk
                        gk_vza = gk
                        if f'raa_{band_ds[b_k]["att"]["wave_name"]}' in l1r_datasets:
                            gk_raa = f'_{band_ds[b_k]["att"]["wave_name"]}' + gk_raa
                        if f'vza_{band_ds[b_k]["att"]["wave_name"]}' in l1r_datasets:
                            gk_vza = f'_{band_ds[b_k]["att"]["wave_name"]}' + gk_vza

                        ## run through two best fitting bands
                        fit_bands = [f'b{bbi + 1}' for bbi in range(setu['dsf_nbands_fit'])]
                        for ai, ab in enumerate(fit_bands):
                            aot_sub = np.where(aot_stack[lut_name][ab] == bi)
                            ## get rhod for current band
                            if (setu['dsf_aot_estimate'] == 'resolved'):
                                rhod_f[aot_sub[0], aot_sub[1], ai] = band_ds[b_k]['data'][aot_sub]
                            elif (setu['dsf_aot_estimate'] == 'segmented'):
                                rhod_f[aot_sub[0], aot_sub[1], ai] = dsf_rhod[b_k][aot_sub].flatten()
                            else:
                                rhod_f[aot_sub[0], aot_sub[1], ai] = dsf_rhod[b_k][aot_sub] # band_data / gas
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
                                                (xi[0][aot_sub], lutdw[lut_name]['ipd'][par], lutdw[lut_name]['meta']['wave'],
                                                 xi[1][aot_sub], xi[2][aot_sub], xi[3][aot_sub], xi[4][aot_sub],
                                                 aot_stack[lut_name]['aot'][aot_sub]))
                                        rhop_f[aot_sub[0], aot_sub[1], ai] = atmos.shared.rsr_convolute_nd(
                                            res_hyp.flatten(), lutdw[lut_name]['meta']['wave'],
                                            rsrd['rsr'][b_k]['response'], rsrd['rsr'][b_k]['wave'], axis=0)
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
                                                rsrd['rsr'][b_k]['response'], rsrd['rsr'][b_k]['wave'], axis=0)
                                else:
                                    if setu['dsf_aot_estimate'] == 'segmented':
                                        for gki in range(len(aot_sub[0])):
                                            rhop_f[aot_sub[0][gki], aot_sub[1][gki], ai] = lutdw[lut_name]['rgi'][b_k](
                                                (xi[0][aot_sub[0][gki]], lutdw[lut_name]['ipd'][par],
                                                 xi[1][aot_sub[0][gki]], xi[2][aot_sub[0][gki]],
                                                 xi[3][aot_sub[0][gki]], xi[4][aot_sub[0][gki]],
                                                 aot_stack[lut_name]['aot'][aot_sub][gki]))

                                    else:
                                        rhop_f[aot_sub[0], aot_sub[1], ai] = lutdw[lut_name]['rgi'][band_num](
                                            (xi[0], lutdw[lut_name]['ipd'][par],
                                             xi[1], xi[2], xi[3], xi[4], aot_stack[lut_name]['aot'][aot_sub]))
                    ## rmsd for current bands
                    cur_sel_par = np.sqrt(np.nanmean(np.square((rhod_f - rhop_f)), axis=2)) # band_data - lut value for aot to trans
                    if (setu['dsf_aot_estimate'] == 'fixed') :
                        print( f'Computing RMSD for model {lut_name}: {cur_sel_par[0][0]:.4e}')

                ## end select with min RMSD

                ## select model based on minimum delta tau between two lowest aot bands
                if setu['dsf_model_selection'] == 'min_dtau':
                    cur_sel_par = aot_stack[lut_name]['dtau']
                ## end select with min delta tau

                ## store minimum info
                if l_i == 0:
                    aot_lut = np.zeros(aot_stack[lut_name]['aot'].shape, dtype=np.float32).astype(int)
                    aot_lut[aot_stack[lut_name]['mask']] = -1
                    aot_sel = aot_stack[lut_name]['aot'] * 1.0
                    aot_sel_par = cur_sel_par * 1.0
                    if setu['dsf_aot_estimate'] == 'fixed':
                        aot_sel_lut = '{}'.format(lut_name)
                        aot_sel_bands = [aot_stack[lut_name][f'{bb}'][0][0] for bb in fit_bands]
                else:
                    aot_sub = np.where(cur_sel_par < aot_sel_par)
                    if len(aot_sub[0]) == 0:
                        continue
                    aot_lut[aot_sub] = l_i
                    aot_sel[aot_sub] = aot_stack[lut_name]['aot'][aot_sub] * 1.0
                    aot_sel_par[aot_sub] = cur_sel_par[aot_sub] * 1.0
                    if setu['dsf_aot_estimate'] == 'fixed':
                        aot_sel_lut = f'{lut_name}'
                        aot_sel_bands = [aot_stack[lut_name][f'{bb}'][0][0] for bb in fit_bands]

            rhod_f = None
            rhod_p = None
        if (setu['dsf_aot_estimate'] == 'fixed') & (aot_sel_par is not None):
            print(f'Selected model {aot_sel_lut}: aot {aot_sel[0][0]:.3f}, RMSD {aot_sel_par[0][0]:.2e}')

        ## check variable aot, use most common LUT
        if (setu['dsf_aot_estimate'] != 'fixed') & (setu['dsf_aot_most_common_model']):
            print('Selecting most common model for processing.')
            n_aot = len(np.where(aot_lut != -1)[0]) # 0 = mod_1, 1 = mod2, -1 = null
            n_sel = 0
            for l_i, lut_name in enumerate(luts):
                sub = np.where(aot_lut == l_i) # get indices where mod type is equal with current mod number
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

    ## exponential
    elif ac_opt == 'exp':
        ## find bands to use
        exp_b1 = None
        exp_b1_diff = 1000
        exp_b2 = None
        exp_b2_diff = 1000
        exp_mask = None
        exp_mask_diff = 1000

        for b_k, b_v in l1r['bands'].items():
            sd = np.abs(b_v['att']['wave_nm'] - setu['exp_wave1'])
            if (sd < 100) & (sd < exp_b1_diff):
                exp_b1_diff = sd
                exp_b1 = b_k
                short_wv = b_v['att']['wave_nm']
            sd = np.abs(b_v['att']['wave_nm'] - setu['exp_wave2'])
            if (sd < 100) & (sd < exp_b2_diff):
                exp_b2_diff = sd
                exp_b2 = b_k
                long_wv = b_v['att']['wave_nm']
            sd = np.abs(b_v['att']['wave_nm'] - setu['l2w_mask_wave'])
            if (sd < 100) & (sd < exp_mask_diff):
                exp_mask_diff = sd
                exp_mask = b_k
                mask_wv = b_v['att']['wave_nm']

        if (exp_b1 is None) or (exp_b2 is None):
            raise ValueError('Stopped: EXP bands not found in L1R bands')

        print(f'Selected bands {exp_b1} and {exp_b2} for EXP processing')
        if (l1r['bands'][exp_b1]['att']['rhot_ds'] not in l1r_datasets) | (l1r['bands'][exp_b2]['att']['rhot_ds'] not in l1r_datasets):
            print(f'Selected bands are not available in {setu["inputfile"]}')
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
            mask = exp_d1 >= setu['exp_swir_threshold']
        elif exp_mask == exp_b2:
            mask = exp_d2 >= setu['exp_swir_threshold']
        else:
            exp_dm = l1r["bands"][exp_mask]["data"] * 1.0
            rorayl_mask = lutdw[exp_lut]['rgi'][exp_mask]((xi[0], lutdw[exp_lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))
            exp_dm -= rorayl_mask
            mask = exp_dm >= setu['exp_swir_threshold']
            exp_dm = None

        ## compute aerosol epsilon band ratio
        epsilon = exp_d1 / exp_d2
        epsilon[np.where(mask)] = np.nan

        ## red/NIR option
        exp_fixed_epsilon = False
        if setu['exp_fixed_epsilon']:
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
            exp_gamma = tr_b1 / tr_b2 if setu['exp_gamma'] is None else float(setu['exp_gamma'])
            print(f'Gamma: {exp_gamma:.2f}')

            ## get alpha
            if setu['exp_alpha'] is None:
                ## import simspec
                simspec = atmos.shared.similarity_read()
                ## convolute to sensor_o
                if setu['exp_alpha_weighted']:
                    ssd = atmos.shared.rsr_convolute_dict(simspec['wave'], simspec['ave'], rsrd['rsr'])
                    exp_alpha = ssd[exp_b1] / ssd[exp_b2]
                ## or use closest bands
                else:
                    ssi0, ssw0 = atmos.shared.closest_idx(simspec['wave'], l1r['bands'][exp_b1]['att']['wave_mu'])
                    ssi1, ssw1 = atmos.shared.closest_idx(simspec['wave'], l1r['bands'][exp_b2]['att']['wave_mu'])
                    exp_alpha = simspec['ave'][ssi0] / simspec['ave'][ssi1]
            else:
                exp_alpha = float(setu['exp_alpha'])
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
            if setu['exp_fixed_aerosol_reflectance']: exp_fixed_epsilon = True

        ## compute fixed epsilon
        if exp_fixed_epsilon:
            if setu['exp_epsilon'] is not None:
                epsilon = float(setu['exp_epsilon'])
            else:
                epsilon = np.nanpercentile(epsilon, setu['exp_fixed_epsilon_percentile'])

        ## determination of rhoam in long wavelength
        if exp_option == 'red/NIR':
            rhoam = (exp_alpha * exp_gamma * exp_d2 - exp_d1) / (exp_alpha * exp_gamma - epsilon)
        else:
            rhoam = exp_d2 * 1.0

        ## clear memory
        exp_d1, exp_d2 = None, None

        ## fixed rhoam?
        exp_fixed_rhoam = setu['exp_fixed_aerosol_reflectance']
        if exp_fixed_rhoam:
            rhoam = np.nanpercentile(rhoam, setu['exp_fixed_aerosol_reflectance_percentile'])
            print(f'{setu["exp_fixed_aerosol_reflectance_percentile"]:.0f}th percentile rhoam ({long_wv} nm): {rhoam:.5f}')

        print('EXP band 1', setu['exp_wave1'], exp_b1, l1r['bands'][exp_b1]['att']['rhot_ds'])
        print('EXP band 2', setu['exp_wave2'], exp_b2, l1r['bands'][exp_b2]['att']['rhot_ds'])

        if exp_fixed_epsilon:
            print(f'Epsilon: {epsilon:.2f}')

        ## output data
        if setu['exp_output_intermediate']:
            if not exp_fixed_epsilon:
                gatts['epsilon'] = epsilon
            if not exp_fixed_rhoam:
                gatts['rhoam'] = rhoam
    ## end exponential

    ## set up interpolator for tiled processing
    if (ac_opt == 'dsf') & (setu['dsf_aot_estimate'] == 'tiled'):
        xnew = np.linspace(0, tiles[-1][1], gatts['data_dimensions'][1], dtype=np.float32)
        ynew = np.linspace(0, tiles[-1][0], gatts['data_dimensions'][0], dtype=np.float32)

    ## store fixed aot in gatts
    if (ac_opt == 'dsf') & (setu['dsf_aot_estimate'] == 'fixed'):
        gatts['ac_aot_550'] = aot_sel[0][0]
        gatts['ac_model'] = luts[aot_lut[0][0]]

        if setu['dsf_fixed_aot'] is None:
            ## store fitting parameter
            gatts['ac_fit'] = aot_sel_par[0][0]
            ## store bands used for DSF
            gatts['ac_bands'] = ','.join([str(b) for b in aot_stack[gatts['ac_model']]['band_list']])
            gatts['ac_nbands_fit'] = setu['dsf_nbands']
            for bbi, bn in enumerate(aot_sel_bands):
                gatts['ac_band{}_idx'.format(bbi + 1)] = aot_sel_bands[bbi]
                gatts['ac_band{}'.format(bbi + 1)] = aot_stack[gatts['ac_model']]['band_list'][
                    aot_sel_bands[bbi]]

    ## write aot to outputfile
    if (ac_opt == 'dsf') & (setu['dsf_write_aot_550']):
        ## reformat & save aot
        if setu['dsf_aot_estimate'] == 'fixed':
            aot_out = np.repeat(aot_sel, gatts['data_elements']).reshape(gatts['data_dimensions'])
        elif setu['dsf_aot_estimate'] == 'segmented':
            aot_out = np.zeros(gatts['data_dimensions']) + np.nan
            for sidx, segment in enumerate(segment_data):
                aot_out[segment_data[segment]['sub']] = aot_sel[sidx]
        elif setu['dsf_aot_estimate'] == 'tiled':
            aot_out = atmos.shared.tiles_interp(aot_sel, xnew, ynew, target_mask=None,
                                             smooth=setu['dsf_tile_smoothing'],
                                             kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                             method=setu['dsf_tile_interp_method'])
        else:
            aot_out = aot_sel * 1.0
        ## write aot
        l2r['aot_550'] = aot_out
        l2r_datasets.append('aot_550')

    ## store ttot for glint correction
    ttot_all = {}

    ## allow use of per pixel geometry for fixed dsf
    if (per_pixel_geometry) & (setu['dsf_aot_estimate'] == 'fixed') & (setu['resolved_geometry']):
        use_revlut = True

    ## for ease of subsetting later, repeat single element datasets to the tile shape
    if (use_revlut) & (ac_opt == 'dsf') & (setu['dsf_aot_estimate'] != 'tiled'):
        for ds in geom_ds:
            if len(np.atleast_1d(data_mem[ds])) != 1:
                continue

            print(f'Reshaping {ds} to {gatts["data_dimensions"][0]}x{gatts["data_dimensions"][1]}')
            data_mem[ds] = np.repeat(data_mem[ds], gatts['data_elements']).reshape(gatts['data_dimensions'])

    ## figure out cirrus bands
    if setu['cirrus_correction']:
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
        for bi, b_k, b_v in enumerate(l1r['bands'].items()):
            band_num = b_k[1:]
            if ('rhot_ds' not in b_v['att']):
                continue
            if b_v['att']['rhot_ds'] not in l1r_datasets:
                continue
            if (b_v['att']['wave_nm'] < setu['cirrus_range'][0]):
                continue
            if (b_v['att']['wave_nm'] > setu['cirrus_range'][1]):
                continue

            ## compute Rayleigh reflectance
            if hyper:
                rorayl_cur = atmos.shared.rsr_convolute_nd(rorayl_hyp, lutdw[luts[0]]['meta']['wave'],
                                                           rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'], axis=0)
            else:
                rorayl_cur = lutdw[luts[0]]['rgi'][b_k]((xi[0], lutdw[luts[0]]['ipd'][par], xi[1], xi[2], xi[3], xi[4], 0.001))

            ## cirrus reflectance = rho_t - rho_Rayleigh
            cur_data = l1r['bands'][b_k]['data'] - rorayl_cur

            if rho_cirrus is None:
                rho_cirrus = cur_data * 1.0
            else:
                rho_cirrus = np.dstack((rho_cirrus, cur_data))
            cur_data = None

        if rho_cirrus is None:
            setu['cirrus_correction'] = False
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
    for bi, (b_k, b_v) in enumerate(l1r['bands'].items()):
        band_num = b_k[1:]
        if ('rhot_ds' not in b_v['att']) or ('tt_gas' not in b_v['att']):
            print(f'Band {b_k} at {b_v["att"]["wave_name"]} nm not in bands dataset')
            continue
        if b_v['att']['rhot_ds'] not in l1r_datasets:
            print(f'Band {b_k} at {b_v["att"]["wave_name"]} nm not in available rhot datasets')
            continue  ## skip if we don't have rhot for a band that is in the RSR file

        ## temporary fix
        if b_v['att']['wave_mu'] < 0.345:
            print(f'Band {b_k} at {b_v["att"]["wave_name"]} nm wavelength < 345 nm')
            continue  ## skip if below LUT range

        rhot_name = b_v['att']['rhot_ds'] # dsi
        rhos_name = b_v['att']['rhos_ds'] # dso
        cur_data, cur_att = b_v['data'].copy(), b_v['att'].copy()

        ## store rhot in output file

        if b_v['att']['tt_gas'] < setu['min_tgas_rho']:
            print(f'Band {b_k} at {b_v["att"]["wave_name"]} nm has tgas < min_tgas_rho ({b_v["att"]["tt_gas"]:.2f} < {setu["min_tgas_rho"]:.2f})')
            continue

        ## apply cirrus correction
        if setu['cirrus_correction']:
            g = setu['cirrus_g_vnir'] * 1.0
            if b_v['att']['wave_nm'] > 1000:
                g = setu['cirrus_g_swir'] * 1.0
            cur_data -= (rho_cirrus * g)

        t0 = time.time()
        print('Computing surface reflectance', b_k, b_v['att']['wave_name'],f'{b_v["att"]["tt_gas"]:.3f}')

        ds_att = b_v['att']
        ds_att['wavelength'] = ds_att['wave_nm']

        ## dark spectrum fitting
        if (ac_opt == 'dsf'):
            if setu['slicing']:
                valid_mask = np.isfinite(cur_data)

            ## shape of atmospheric datasets
            atm_shape = aot_sel.shape

            ## if path reflectance is resolved, but resolved geometry available
            if (use_revlut) & (setu['dsf_aot_estimate'] == 'fixed'):
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

            if (setu['dsf_residual_glint_correction']) & (setu['dsf_residual_glint_correction_method'] == 'default'):
                ttot_all[b_k] = np.zeros(atm_shape, dtype=np.float32) + np.nan

            for li, lut in enumerate(luts):
                ls = np.where(aot_lut == li)
                if len(ls[0]) == 0:
                    continue
                ai = aot_sel[ls]

                ## resolved geometry with fixed path reflectance
                if (use_revlut) & (setu['dsf_aot_estimate'] == 'fixed'):
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
                    if (setu['dsf_residual_glint_correction']) & (
                            setu['dsf_residual_glint_correction_method'] == 'default'):
                        ttot_all[b_k][ls] = atmos.shared.rsr_convolute_nd(hyper_res['ttot'], lutdw[lut]['meta']['wave'],
                                                                     rsrd['rsr'][band_num]['response'], rsrd['rsr'][band_num]['wave'],
                                                                     axis=0)
                else:
                    ## path reflectance
                    romix[ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd'][par], xi[1], xi[2], xi[3], xi[4], ai))

                    ## transmittance and spherical albedo
                    astot[ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd']['astot'], xi[1], xi[2], xi[3], xi[4], ai))
                    dutott[ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd']['dutott'], xi[1], xi[2], xi[3], xi[4], ai))

                    ## total transmittance
                    if (setu['dsf_residual_glint_correction']) & (setu['dsf_residual_glint_correction_method'] == 'default'):
                        ttot_all[b_k][ls] = lutdw[lut]['rgi'][band_num]((xi[0], lutdw[lut]['ipd']['ttot'], xi[1], xi[2], xi[3], xi[4], ai))
                del ls, ai, xi

            ## interpolate tiled processing to full scene
            if setu['dsf_aot_estimate'] == 'tiled':
                print('Interpolating tiles')
                romix = atmos.shared.tiles_interp(romix, xnew, ynew, target_mask=(valid_mask if setu['slicing'] else None), \
                                               target_mask_full=True, smooth=setu['dsf_tile_smoothing'],
                                               kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                               method=setu['dsf_tile_interp_method'])
                astot = atmos.shared.tiles_interp(astot, xnew, ynew, target_mask=(valid_mask if setu['slicing'] else None), \
                                               target_mask_full=True, smooth=setu['dsf_tile_smoothing'],
                                               kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                               method=setu['dsf_tile_interp_method'])
                dutott = atmos.shared.tiles_interp(dutott, xnew, ynew,
                                                target_mask=(valid_mask if setu['slicing'] else None), \
                                                target_mask_full=True, smooth=setu['dsf_tile_smoothing'],
                                                kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                                method=setu['dsf_tile_interp_method'])

            ## create full scene parameters for segmented processing
            if setu['dsf_aot_estimate'] == 'segmented':
                romix_ = romix * 1.0
                astot_ = astot * 1.0
                dutott_ = dutott * 1.0
                romix = np.zeros(gatts['data_dimensions']) + np.nan
                astot = np.zeros(gatts['data_dimensions']) + np.nan
                dutott = np.zeros(gatts['data_dimensions']) + np.nan

                for sidx, segment in enumerate(segment_data):
                    romix[segment_data[segment]['sub']] = romix_[sidx]
                    astot[segment_data[segment]['sub']] = astot_[sidx]
                    dutott[segment_data[segment]['sub']] = dutott_[sidx]
                del romix_, astot_, dutott_

            ## write ac parameters
            if setu['dsf_write_tiled_parameters']:
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
        if (setu['output_rhorc']):
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
            if setu['dsf_aot_estimate'] == 'segmented':
                rorayl_ = rorayl_cur * 1.0
                dutotr_ = dutotr_cur * 1.0
                rorayl_cur = np.zeros(gatts['data_dimensions']) + np.nan
                dutotr_cur = np.zeros(gatts['data_dimensions']) + np.nan
                for sidx, segment in enumerate(segment_data):
                    rorayl_cur[segment_data[segment]['sub']] = rorayl_[sidx]
                    dutotr_cur[segment_data[segment]['sub']] = dutotr_[sidx]
                del rorayl_, dutotr_

            ## create full scene parameters for tiled processing
            if (setu['dsf_aot_estimate'] == 'tiled') & (use_revlut):
                print('Interpolating tiles for rhorc')
                rorayl_cur = atmos.shared.tiles_interp(rorayl_cur, xnew, ynew,
                                                    target_mask=(valid_mask if setu['slicing'] else None), \
                                                    target_mask_full=True, smooth=setu['dsf_tile_smoothing'],
                                                    kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                                    method=setu['dsf_tile_interp_method'])
                dutotr_cur = atmos.shared.tiles_interp(dutotr_cur, xnew, ynew,
                                                    target_mask=(valid_mask if setu['slicing'] else None), \
                                                    target_mask_full=True, smooth=setu['dsf_tile_smoothing'],
                                                    kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                                    method=setu['dsf_tile_interp_method'])

            ## write ac parameters
            if setu['dsf_write_tiled_parameters']:
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

        if ac_opt == 'dsf' and setu['slicing']:
            del valid_mask

        ## write rhos
        l2r['bands'][b_k] = {'data': cur_data, 'att': ds_att}
        rhos_to_band_name[b_v['att']['rhos_ds']] = b_k
        l2r_datasets.append(rhos_name)

        del cur_data
        print(f'{gatts["sensor"]}/{b_k} took {(time.time() - t0):.1f}s ({"RevLUT" if use_revlut else "StdLUT"})')

    ## glint correction
    if (ac_opt == 'dsf') & (setu['dsf_residual_glint_correction']) & ( setu['dsf_residual_glint_correction_method'] == 'default'):
        ## find bands for glint correction
        gc_swir1, gc_swir2 = None, None
        gc_swir1_b, gc_swir2_b = None, None
        swir1d, swir2d = 1000, 1000
        gc_user, gc_mask = None, None
        gc_user_b, gc_mask_b = None, None
        userd, maskd = 1000, 1000
        for b_k, b_v in l2r['bands'].items():

            ## swir1
            sd = np.abs(b_v['att']['wave_nm'] - 1600)
            if sd < 100:
                if sd < swir1d:
                    gc_swir1 = b_v['att']['rhos_ds']
                    swir1d = sd
                    gc_swir1_b = b_k
            ## swir2
            sd = np.abs(b_v['att']['wave_nm'] - 2200)
            if sd < 100:
                if sd < swir2d:
                    gc_swir2 = b_v['att']['rhos_ds']
                    swir2d = sd
                    gc_swir2_b = b_k
            ## mask band
            sd = np.abs(b_v['att']['wave_nm'] - setu['glint_mask_rhos_wave'])
            if sd < 100:
                if sd < maskd:
                    gc_mask = b_v['att']['rhos_ds']
                    maskd = sd
                    gc_mask_b = b_k
            ## user band
            if setu['glint_force_band'] is not None:
                sd = np.abs(b_v['att']['wave_nm'] - setu['glint_force_band'])
                if sd < 100:
                    if sd < userd:
                        gc_user = b_v['att']['rhos_ds']
                        userd = sd
                        gc_user_b = b_k

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
                sub_gc = np.where(np.isfinite(gc_mask_data) & (gc_mask_data <= setu['glint_mask_rhos_threshold']))
                del gc_mask_data

                ## get reference bands transmittance
                for ib, (b_k, b_v) in enumerate(l2r['bands'].items()):
                    rhos_ds = b_v['att']['rhos_ds']
                    if rhos_ds not in [gc_swir1, gc_swir2, gc_user]:
                        continue
                    if rhos_ds not in l2r_datasets:
                        continue

                    ## two way direct transmittance
                    if setu['dsf_aot_estimate'] == 'tiled':
                        if setu['slicing']:
                            ## load rhos dataset
                            cur_data = l2r['bands'][b_k]['data'].copy()
                            valid_mask = np.isfinite(cur_data)
                            del cur_data
                        ttot_all_b = atmos.shared.tiles_interp(ttot_all[b_k], xnew, ynew,
                                                            target_mask=(valid_mask if setu['slicing'] else None), \
                                                            target_mask_full=True,
                                                            smooth=setu['dsf_tile_smoothing'],
                                                            kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                                            method=setu['dsf_tile_interp_method'])
                    elif setu['dsf_aot_estimate'] == 'segmented':
                        ttot_all_ = ttot_all[b] * 1.0
                        ttot_all_b = np.zeros(gatts['data_dimensions']) + np.nan
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
                for ib, (b_k, b_v) in enumerate(l2r['bands'].items()):
                    rhos_ds = b_v['att']['rhos_ds']
                    if rhos_ds not in l2r_datasets:
                        continue
                    if b_k not in ttot_all:
                        continue
                    print(f'Performing glint correction for band {b_k} ({b_v["att"]["wave_name"]} nm)')
                    ## load rhos dataset
                    cur_data = l2r['bands'][b_k]['data'].copy()

                    ## two way direct transmittance
                    if setu['dsf_aot_estimate'] == 'tiled':
                        if setu['slicing']:
                            valid_mask = np.isfinite(cur_data)
                        ttot_all_b = atmos.shared.tiles_interp(ttot_all[b_k], xnew, ynew,
                                                            target_mask=(valid_mask if setu['slicing'] else None), \
                                                            target_mask_full=True,
                                                            smooth=setu['dsf_tile_smoothing'],
                                                            kern_size=setu['dsf_tile_smoothing_kernel_size'],
                                                            method=setu['dsf_tile_interp_method'])
                    elif setu['dsf_aot_estimate'] == 'segmented':
                        ttot_all_ = ttot_all[b_k] * 1.0
                        ttot_all_b = np.zeros(gatts['data_dimensions']) + np.nan
                        for sidx, segment in enumerate(segment_data):
                            ttot_all_b[segment_data[segment]['sub']] = ttot_all_[sidx]
                        del ttot_all_
                    else:
                        ttot_all_b = ttot_all[b_k] * 1.0
                    if setu['dsf_write_tiled_parameters']:
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
                    Rf_sen_cur = atmos.ac.sky_refl(omega, n_w=refri_sen[b_k[1:]])

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
                        if setu['glint_write_rhog_ref']:
                            tmp = np.zeros(gatts['data_dimensions'], dtype=np.float32) + np.nan
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
                    if setu['glint_write_rhog_all']:
                        tmp = np.zeros(gatts['data_dimensions'], dtype=np.float32) + np.nan
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
        if (setu['dsf_aot_estimate'] == 'tiled') & (setu['slicing']):
            del valid_mask
    ## end glint correction

    ## alternative glint correction
    if (ac_opt == 'dsf') & (setu['dsf_residual_glint_correction']) & (setu['dsf_aot_estimate'] in ['fixed', 'segmented']) & \
            (setu['dsf_residual_glint_correction_method'] == 'alternative'):

        ## reference aot and wind speed
        if setu['dsf_aot_estimate'] == 'fixed':
            gc_aot = max(0.1, gatts['ac_aot_550'])
            gc_wind = 20
            gc_lut = gatts['ac_model']

            raa = gatts['raa']
            sza = gatts['sza']
            vza = gatts['vza']

            ## get surface reflectance for fixed geometry
            if len(np.atleast_1d(raa)) == 1:
                if hyper:
                    surf = lutdw[gc_lut]['rgi']((gatts['pressure'], lutdw[gc_lut]['ipd']['rsky_s'], lutdw[gc_lut]['meta']['wave'], raa, vza, sza, gc_wind, gc_aot))
                    surf_res = atmos.shared.rsr_convolute_dict(lutdw[gc_lut]['meta']['wave'], surf, rsrd['rsr'])
                else:
                    surf_res = {b: lutdw[gc_lut]['rgi'][b]((gatts['pressure'], lutdw[gc_lut]['ipd']['rsky_s'], raa, vza, sza, gc_wind, gc_aot)) for b in lutdw[gc_lut]['rgi']}

        if setu['dsf_aot_estimate'] == 'segmented':
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
        for ib, (b_k, b_v) in enumerate(l2r["bands"].items()):
            band_num = b_k[1:]
            rhos_ds = b_v['att']['rhos_ds']
            if rhos_ds not in l2r_datasets:
                continue
            if (b_v['att']['wavelength'] < setu['dsf_residual_glint_wave_range'][0]) | \
                    (b_v['att']['wavelength'] > setu['dsf_residual_glint_wave_range'][1]):
                continue

            print(f'Reading reference for glint correction from band {b_k} ({b_v["att"]["wave_name"]} nm)')

            if setu['dsf_aot_estimate'] == 'fixed':
                gc_sur_cur = surf_res[band_num]
            if setu['dsf_aot_estimate'] == 'segmented':
                gc_sur_cur = l2r['bands'][b_k] * np.nan
                for segment in segment_data:
                    gc_sur_cur[segment_data[segment]['sub']] = surf_res[segment][band_num]

            if gc_ref is None:
                gc_ref = b_v['data'] * 1.0
                gc_sur = gc_sur_cur
            else:
                gc_ref = np.dstack((gc_ref, b_v['data'] * 1.0))
                gc_sur = np.dstack((gc_sur, gc_sur_cur))

        if gc_ref is None:
            print(f'No bands found between {setu["dsf_residual_glint_wave_range"][0]} and {setu["dsf_residual_glint_wave_range"][1]} nm for glint correction')
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
            if setu['dsf_aot_estimate'] == 'segmented':
                axis = 2
            gc_sur_mean = np.nanmean(gc_sur, axis=axis)
            gc_sur_std = np.nanstd(gc_sur, axis=axis)

            ## get subset where to apply glint correction
            gc_sub = np.where(gc_ref_mean < setu['glint_mask_rhos_threshold'])

            ## glint correction per band
            for ib, (b_k, b_v) in enumerate(l2r['bands'].items()):
                rhos_ds = b_v['att']['rhos_ds']
                band_name = b_k[1:]
                if rhos_ds not in l2r_datasets:
                    continue
                print(f'Performing glint correction for band {b_k} ({b_v["att"]["wave_name"]} nm)')

                ## estimate current band glint from reference glint image and ratio of interface reflectance
                if setu['dsf_aot_estimate'] == 'fixed':
                    sur = surf_res[band_name] * 1.0

                if setu['dsf_aot_estimate'] == 'segmented':
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
                if setu['glint_write_rhog_all']:
                    tmp = np.zeros(gatts['data_dimensions'], dtype=np.float32) + np.nan
                    tmp[gc_sub] = cur_rhog
                    rhog_key = f'rhog_{b_v["att"]["wave_name"]}'
                    l2r[rhog_key] = {}
                    l2r[rhog_key]['data'] = tmp
                    l2r[rhog_key]['att'] = {'wavelength': b_v['att']['wavelength']}
                    tmp = None
                cur_rhog = None
    ## end alternative glint correction

    return l2r
