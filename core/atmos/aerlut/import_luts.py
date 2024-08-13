## read all luts and set up rgi
## QV 2020-01-15
## Last modifications: 2020-07-14 (QV) added sensor option
##                     2020-07-14 (QV) changed sensor option to a dict per band
##                     2020-07-22 (QV) added the rsky lut to the lut and rgi - need to update rsky azimuths
##                     2020-07-25 (QV) added updates to rsky lut
##                     2021-01-19 (QV) update to new LUTs
##                     2021-02-01 (QV) added wind speed for rsky lut, removed temp fixes for old luts
##                     2021-02-03 (QV) added down*up total transmittances
##                     2021-03-01 (QV) added new rsky luts with integrated wind speed
##                     2021-06-08 (QV) added lut par subsetting
##                     2021-10-24 (QV) added get_remote as keyword
##                     2021-11-09 (QV) added reduce dimensions
##                     2022-03-03 (QV) increased default reduce dimensions AOT range
##                     2024-04-25 (QV) check par/add_rsky combination, check wnd dimensions
##                                     separate function for merging luts - which is not faster (maybe depending on disk speed?)

import scipy.interpolate
import numpy as np
import core.atmos as atmos
from core.util import rsr_read

def import_luts(pressures = [500, 750, 1013, 1100],
                base_luts = ['ACOLITE-LUT-202110-MOD1', 'ACOLITE-LUT-202110-MOD2'],
                rsky_lut_name ='ACOLITE-RSKY-202102-82W',
                lut_par = ['utott', 'dtott', 'astot', 'ttot', 'romix'],
                reduce_dimensions = False, return_lut_array = False,
                par = 'romix',
                vza_range = [0, 16], aot_range = [0, 1.5],
                use_merged_lut = False, store_merged_lut = False,
                get_remote = True, sensor = None, add_rsky = False, add_dutott = True):

    ## indices for reducing LUT size
    vza_sub = [0, -1]
    aot_sub = [0, -1]

    if par not in ['romix+rsky_t', 'romix+rsurf']:
        add_rsky = False

    if add_rsky:
        klist = ['utott', 'dtott', 'astot', 'romix']
        if par == 'romix+rsky_t' and use_merged_lut:
            klist += ['romix+rsky_t']

        if par == 'romix+rsurf':
            klist += ['rsurf']

        for k in klist:
            if k not in lut_par:
                lut_par.append(k)
    if add_dutott:
        for k in ['utott', 'dtott']:
            if k not in lut_par:
                lut_par.append(k)

    lut_dict = {}
    ## run through luts
    for lut in base_luts:
        ## run through pressures
        for ip, pr in enumerate(pressures):
            lutid = f'{lut}-{f"{pr}".zfill(4)}mb'
            lutdir = f'{atmos.config["lut_dir"]}/{"-".join(lutid.split("-")[0:3])}'

            if sensor is None:
                ## indices for reducing LUT size
                vza_idx, aot_idx = 4, 7
                if not add_rsky:
                    aot_idx = 6
                if add_rsky and (par == 'romix+rsky_t') and use_merged_lut: ## load merged lut
                    lut_data, lut_meta = atmos.aerlut.merged_lut(lut, rsky_lut_name, pr, sensor = sensor, store = store_merged_lut, lut_par = lut_par, get_remote = get_remote)
                else:
                    lut_data, lut_meta = atmos.aerlut.import_lut(lutid, lutdir, sensor = sensor, lut_par = lut_par, get_remote = get_remote)
            else:
                ## indices for reducing LUT size
                vza_idx, aot_idx = 3, 6
                if not add_rsky:
                    aot_idx = 5

                # param maps for utott(up-ward total transmittion), dtott(down-ward), astot(total scattering coef), romix(rho for mixture), ttot(total transmission) using 5 different variables(azi, thv, ths, wind, tau)
                if add_rsky and (par == 'romix+rsky_t') and use_merged_lut:  ## load merged lut
                    lut_data_dict, lut_meta = atmos.aerlut.merged_lut(lut, rsky_lut_name, pr, sensor=sensor, store=store_merged_lut, lut_par=lut_par, get_remote=get_remote)
                else:
                    lut_data_dict, lut_meta = atmos.aerlut.import_lut(lutid, lutdir, sensor=sensor, lut_par=lut_par, get_remote=get_remote)

                if 'bands' not in lut_meta:
                    # get bands from rsr_file as different systems may not keep dict keys in the same order
                    rsr_file = atmos.config['data_dir']+'/RSR/'+sensor+'.txt'
                    # rsr contains response functions for each band, and rsr_bands contains the band numbers
                    rsr, rsr_bands = rsr_read(file=rsr_file)

                else:
                    rsr_bands = lut_meta['bands']

            ## set up lut dimensions
            if ip == 0:
                # lut data is par, wave, azi, thv, ths, wind, tau
                lut_dim = [[i for i in pressures]] + [[i for i in range(len(lut_meta['par']))]]
                if sensor is None:
                    lutd = []
                    lut_dim += [lut_meta['wave']]
                if (add_rsky) and (par == 'romix+rsky_t') and (use_merged_lut): ## add wind dimension
                    lut_dim += [lut_meta[k] for k in ['azi', 'thv', 'ths', 'wnd', 'tau']]
                else:
                    lut_dim += [lut_meta[k] for k in ['azi', 'thv', 'ths', 'tau']]
                ipd = {par:ip for ip,par in enumerate(lut_meta['par'])}

                # lut_meta = input vars for lut, lut_dim = dimensions for lut, ipd = index for parameters
                lut_dict[lut] = {'meta':lut_meta, 'dim':lut_dim, 'ipd':ipd}

                ## find indices to reduce dimensions
                if reduce_dimensions:
                    for vi, v in enumerate(lut_meta['thv']):
                        if v <= vza_range[0]:
                            vza_sub[0] = vi
                        if (v >= vza_range[1]) and (vza_sub[1] == -1):
                            vza_sub[1] = vi+1
                    for vi, v in enumerate(lut_meta['tau']):
                        if v <= aot_range[0]:
                            aot_sub[0] = vi
                        if (v >= aot_range[1]) and (aot_sub[1] == -1):
                            aot_sub[1] = vi+1

                if sensor is not None:
                    lut_dict[lut]['lut'] = {band:[] for band in rsr_bands}

            if sensor is None:
                lutd.append(lut_data)
            else:
                for band in rsr_bands:
                    lut_dict[lut]['lut'][band].append(lut_data_dict[band]) # lut_dict(lut_type:MOD_n, pressure, meta, dim, param_index_map, lut_data)

        ## generic LUT
        if sensor is None:
            lut_dict[lut]['lut'] = np.stack(lutd)
            ipd = lut_dict[lut]['ipd']

            if (add_rsky) and (par == 'romix+rsky_t') and (not use_merged_lut):
                tlut = lut_dict[lut]['lut']
                rskyd = atmos.aerlut.import_rsky_luts(models=[int(lut[-1])], lutbase=rsky_lut_name, get_remote = get_remote)
                rsky_lut = rskyd[int(lut[-1])]['lut']
                rsky_winds  = rskyd[int(lut[-1])]['meta']['wind']
                rskyd = None

                ## repeat 6sv lut for winds
                tlut = np.repeat(tlut, len(rsky_winds), axis=-2)

                ## repeat for pressures
                rsky_lut = np.repeat(rsky_lut[np.newaxis,:], len(pressures), axis=0)

                ## add to the LUT
                ## model rsky at surface
                sky_i = len(ipd)
                tlut = np.insert(tlut, (sky_i), rsky_lut, axis=1)

                ## model rsky at toa
                ## (utott * dtott * rsky) / (1. - rsky * astot)
                tmp_sky = (tlut[:, ipd['utott'],:,:,:,:,:]*\
                       tlut[:, ipd['dtott'],:,:,:,:,:]*
                       tlut[:, sky_i,:,:,:,:,:]) /\
                       (1.-tlut[:, sky_i,:,:,:,:,:] *\
                       tlut[:, ipd['astot'],:,:,:,:,:])
                tlut = np.insert(tlut, (sky_i+1), tmp_sky, axis=1)

                ## add romix+rsky
                tmp_sky = tlut[:, ipd['romix'],:,:,:,:,:] + tlut[:, sky_i+1,:,:,:,:,:]
                tlut = np.insert(tlut, (sky_i+2), tmp_sky, axis=1)

                ## replace lut and add these parameters
                lut_dict[lut]['lut'] = tlut
                lut_dict[lut]['meta']['par'] += ['rsky_s', 'rsky_t', 'romix+rsky_t']
                lut_dict[lut]['ipd'] = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}
                lut_dict[lut]['dim'][1]+= [sky_i, sky_i+1, sky_i+2]
                ## end add rsky

                ## create new dim with winds
                dim = [np.asarray(pressures),
                       np.asarray(lut_dict[lut]['dim'][1]),
                       lut_dict[lut]['meta']['wave'],
                       lut_dict[lut]['meta']['azi'],
                       lut_dict[lut]['meta']['thv'],
                       lut_dict[lut]['meta']['ths'],
                       np.asarray(rsky_winds),
                       lut_dict[lut]['meta']['tau']]
                lut_dict[lut]['dim'] = dim
                ## end add rsky romix+rsky_t

            if (add_rsky) and (par == 'romix+rsurf'):
                sky_i = len(ipd)
                tmp_sky = lut_dict[lut]['lut'][:, ipd['romix'],:,:,:,:,:] + lut_dict[lut]['lut'][:, ipd['rsurf'],:,:,:,:,:]
                lut_dict[lut]['lut'] = np.insert(lut_dict[lut]['lut'], (sky_i), tmp_sky, axis=1)
                tmp_sky = None
                lut_dict[lut]['meta']['par'] += ['romix+rsurf']
                lut_dict[lut]['ipd'] = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}
                lut_dict[lut]['dim'][1]+= [sky_i]
                ## create new dim with winds
                dim = [np.asarray(pressures),
                       np.asarray(lut_dict[lut]['dim'][1]),
                       lut_dict[lut]['meta']['wave'],
                       lut_dict[lut]['meta']['azi'],
                       lut_dict[lut]['meta']['thv'],
                       lut_dict[lut]['meta']['ths'],
                       np.atleast_1d(lut_dict[lut]['meta']['wnd']),
                       lut_dict[lut]['meta']['tau']]
                lut_dict[lut]['dim'] = dim

            ## reduce dimensions / memory use
            if reduce_dimensions:
                lut_dict[lut]['dim'][vza_idx] = lut_dict[lut]['dim'][vza_idx][vza_sub[0]:vza_sub[1]]
                lut_dict[lut]['dim'][aot_idx] = lut_dict[lut]['dim'][aot_idx][aot_sub[0]:aot_sub[1]]
                lut_dict[lut]['lut'] = lut_dict[lut]['lut'][:,:,:,:,vza_sub[0]:vza_sub[1],:,:,aot_sub[0]:aot_sub[1]]

            ## add product of transmittances
            if add_dutott:
                lut_dict[lut]['meta']['par']+=['dutott']
                sky_i = int(lut_dict[lut]['dim'][1][-1])+1
                lut_dict[lut]['dim'][1]=np.append(lut_dict[lut]['dim'][1],sky_i)
                lut_dict[lut]['ipd'] = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}
                iu = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}['utott']
                id = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}['dtott']
                tmp_sky = lut_dict[lut]['lut'][:,iu,:,:,:,:,:,:]*lut_dict[lut]['lut'][:,id,:,:,:,:,:,:]
                lut_dict[lut]['lut'] = np.insert(lut_dict[lut]['lut'], (sky_i), tmp_sky, axis=1)

            ## set up LUT interpolator
            if add_rsky:
                lut_dict[lut]['rgi'] = scipy.interpolate.RegularGridInterpolator(lut_dict[lut]['dim'],
                                                                             lut_dict[lut]['lut'][:,:,:,:,:,:,:,:],
                                                                             bounds_error=False, fill_value=np.nan)
            else:
                lut_dict[lut]['rgi'] = scipy.interpolate.RegularGridInterpolator(lut_dict[lut]['dim'],
                                                                             lut_dict[lut]['lut'][:,:,:,:,:,:,0,:],
                                                                             bounds_error=False, fill_value=np.nan)
        else:
            ## make arrays
            for band in rsr_bands:
                # stack each band data in pressure dimension (4, 5, 13, 13, 16, 1, 16) (pressure, par, wave, azi, thv, ths, wind, tau)
                lut_dict[lut]['lut'][band] = np.stack(lut_dict[lut]['lut'][band])

            ## add rsky if requested
            if (add_rsky) and (par == 'romix+rsky_t') and (not use_merged_lut):
                # get x(including tau), y(lut), meta, rgi funcs for sky reflectance
                rskyd = atmos.aerlut.import_rsky_luts(models=[int(lut[-1])], lutbase=rsky_lut_name, sensor=sensor, get_remote=get_remote)
                rsky_lut = rskyd[int(lut[-1])]['lut']
                if 'wind' in rskyd[int(lut[-1])]['meta']:
                    rsky_winds = rskyd[int(lut[-1])]['meta']['wind']
                else:
                    rsky_winds = np.atleast_1d([0,20])
                #rskyd = None

                ## current pars
                ipd = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}

                ## run through bands
                for band in rsky_lut:
                    tlut = lut_dict[lut]['lut'][band]
                    tmp_sky = rsky_lut[band] * 1.0

                    ## add wind axis
                    if 'wind' not in rskyd[int(lut[-1])]['meta']:
                        tmp_sky = np.expand_dims(tmp_sky, -2)
                        tmp_sky = np.repeat(tmp_sky, len(rsky_winds), axis=-2)
                    tlut = np.repeat(tlut, len(rsky_winds), axis=-2)

                    ## add to the LUT
                    ## model rsky at surface
                    sky_i = len(ipd)
                    tlut = np.insert(tlut, (sky_i), tmp_sky, axis=1) # pressure(4), var(+sky)(6), azi(13), thv(13), ths(16), wind(8), tau(16)

                    ## model rsky at toa
                    ## (utott * dtott * rsky) / (1. - rsky * astot)
                    tmp_sky = (tlut[:, ipd['utott'],:,:,:,:,:] * tlut[:, ipd['dtott'],:,:,:,:,:] * tlut[:, sky_i,:,:,:,:,:]) / \
                              (1. - tlut[:, sky_i,:,:,:,:,:] * tlut[:, ipd['astot'],:,:,:,:,:])
                    tlut = np.insert(tlut, (sky_i+1), tmp_sky, axis=1)

                    ## add romix+rsky
                    tmp_sky = tlut[:, ipd['romix'],:,:,:,:,:] + tlut[:, sky_i+1,:,:,:,:,:]
                    tlut = np.insert(tlut, (sky_i+2), tmp_sky, axis=1)

                    ## replace in dict
                    lut_dict[lut]['lut'][band] = tlut

                ## add new pars
                lut_dict[lut]['meta']['par'] += ['rsky_s', 'rsky_t', 'romix+rsky_t']
                lut_dict[lut]['dim'][1]+= [sky_i, sky_i+1, sky_i+2]

                ## create new dim with winds
                dim = [np.asarray(pressures),
                       np.asarray(lut_dict[lut]['dim'][1]),
                       lut_dict[lut]['meta']['azi'],
                       lut_dict[lut]['meta']['thv'],
                       lut_dict[lut]['meta']['ths'],
                       np.asarray(rsky_winds),
                       lut_dict[lut]['meta']['tau']]
                lut_dict[lut]['dim'] = dim
                ## end add rsky

            if add_rsky and par == 'romix+rsurf':
                ## current pars
                ipd = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}
                sky_i = len(ipd)

                ## run through bands
                for band in lut_dict[lut]['lut']:
                    tmp_sky = lut_dict[lut]['lut'][band][:, ipd['romix'],:,:,:,:] + lut_dict[lut]['lut'][band][:, ipd['rsurf'],:,:,:,:]
                    lut_dict[lut]['lut'][band] = np.insert(lut_dict[lut]['lut'][band], (sky_i), tmp_sky, axis=1)
                    tmp_sky = None
                lut_dict[lut]['meta']['par'] += ['romix+rsurf']
                lut_dict[lut]['ipd'] = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}
                lut_dict[lut]['dim'][1]+= [sky_i]
                ## create new dim with winds
                dim = [np.asarray(pressures),
                       np.asarray(lut_dict[lut]['dim'][1]),
                       lut_dict[lut]['meta']['azi'],
                       lut_dict[lut]['meta']['thv'],
                       lut_dict[lut]['meta']['ths'],
                       np.atleast_1d(lut_dict[lut]['meta']['wnd']),
                       lut_dict[lut]['meta']['tau']]
                lut_dict[lut]['dim'] = dim

            ## reduce dimensions / memory use
            if reduce_dimensions:
                lut_dict[lut]['dim'][vza_idx] = lut_dict[lut]['dim'][vza_idx][vza_sub[0]:vza_sub[1]]
                lut_dict[lut]['dim'][aot_idx] = lut_dict[lut]['dim'][aot_idx][aot_sub[0]:aot_sub[1]]
                for band in rsr_bands:
                    lut_dict[lut]['lut'][band] = lut_dict[lut]['lut'][band][:,:,:,vza_sub[0]:vza_sub[1],:,:,aot_sub[0]:aot_sub[1]]

            ## add product of transmittances
            if add_dutott:
                lut_dict[lut]['meta']['par']+=['dutott']
                dutott_i = int(lut_dict[lut]['dim'][1][-1])+1
                lut_dict[lut]['dim'][1]=np.append(lut_dict[lut]['dim'][1],dutott_i)
                iu = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}['utott']
                id = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}['dtott']
                for band in rsr_bands:
                    dutott = lut_dict[lut]['lut'][band][:,iu,:,:,:,:,:]*lut_dict[lut]['lut'][band][:,id,:,:,:,:,:] # dtott * utott
                    lut_dict[lut]['lut'][band] = np.insert(lut_dict[lut]['lut'][band], (dutott_i), dutott, axis=1)

            lut_dict[lut]['rgi'] = {}
            lut_dict[lut]['ipd'] = {p:i for i,p in enumerate(lut_dict[lut]['meta']['par'])}
            for band in rsr_bands:
                ## set up LUT interpolator per band
                if add_rsky:
                    lut_dict[lut]['rgi'][band] = scipy.interpolate.RegularGridInterpolator(lut_dict[lut]['dim'],
                                                                                       lut_dict[lut]['lut'][band][:,:,:,:,:,:,:],
                                                                                       bounds_error=False, fill_value=np.nan)
                else:
                    lut_dict[lut]['rgi'][band] = scipy.interpolate.RegularGridInterpolator(lut_dict[lut]['dim'],
                                                                                       lut_dict[lut]['lut'][band][:,:,:,:,:,0,:],
                                                                                       bounds_error=False, fill_value=np.nan)
    ## remove LUT array to reduce memory use
    if not return_lut_array:
        for lut in lut_dict:
            del lut_dict[lut]['lut']
    # utott(0), dtott(1), astot(2), ttot(3), romix(4), rsky_s(5), rsky_t(6), romix+rsky_t(7), dutott(8)
    return(lut_dict)
