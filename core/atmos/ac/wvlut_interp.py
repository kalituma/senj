import os, sys
import scipy.interpolate
import numpy as np
from core import atmos

def wvlut_interp(ths, thv, uwv=1.5, sensor=None, config='201710C',
                 par_id = 2, ## old LUT ttwava index
                 pressure = 1013, par = 'ttwava', ## new LUT, index computed
                 remote_base = None):

    ## use URL from main config
    if remote_base is None:
        remote_base = f'{atmos.config["lut_url"]}'

    ## input geometry dimensions
    dim = np.atleast_1d(ths).shape
    dim2 = np.atleast_1d(uwv).shape
    onedim = ((len(dim) == 1) & (dim[0] == 1)) & ((len(dim2) == 1) & (dim2[0] == 1))

    lut_path = f'{atmos.config["data_dir"]}/LUT/WV'
    lut_id = f'WV_{config}'
    lutnc = f'{lut_path}/{lut_id}.nc'

    ## try downloading LUT from GitHub
    if (not os.path.isfile(lutnc)):
        remote_lut = f'{remote_base}/WV/{os.path.basename(lutnc)}'
        try:
            print(f'Getting remote LUT {remote_lut}')
            atmos.shared.download_file(remote_lut, lutnc)
            print(f'Testing LUT {lutnc}')
            lut, meta = atmos.shared.lutnc_import(lutnc) # test LUT
        except:
            print(f'Could not download remote lut {remote_lut} to {lutnc}')
            if os.path.exists(lutnc): os.remove(lutnc)

    ## import LUT
    if os.path.exists(lutnc):
        lut, meta = atmos.shared.lutnc_import(lutnc)
    else:
        print(f'Could not open WV LUT {lutnc}')
        sys.exit(1)

    # find RSR
    if sensor is not None:
        rsrd = atmos.shared.rsr_dict(sensor=sensor)
        if sensor in rsrd:
            rsr, rsr_bands = rsrd[sensor]['rsr'], rsrd[sensor]['rsr_bands']
        else:
            print(f'Sensor {sensor} RSR not found')
            sys.exit(1)

    if onedim:
        ## interpolate hyperspectral dataset
        ## old LUT
        if config=='201710C':
            rgi = scipy.interpolate.RegularGridInterpolator([meta['ths'], meta['thv'], meta['wv'], range(3),
                                                             meta['wave']],lut,
                                                             bounds_error=False, fill_value=None)
            iw = rgi((ths, thv, uwv, par_id, meta['wave']))
        ## new LUT
        else:
            ipd = {p:pi for pi, p in enumerate(meta['par'])}
            rgi = scipy.interpolate.RegularGridInterpolator([meta['pressure'], range(len(meta['par'])),
                                                             meta['wave'], meta['vza'], meta['sza'], meta['wv']],lut,
                                                                 bounds_error=False, fill_value=None)
            iw = rgi((pressure, ipd[par], meta['wave'], thv, ths, uwv))

        if sensor is None:
            ## return hyperspectral dataset for this geometry
            return(meta["wave"], iw)
        else:
            ## make band averaged values
            band_averaged = atmos.shared.rsr_convolute_dict(meta['wave'], iw, rsr)
            return(band_averaged)
    else:
        ## make band averaged values
        if sensor == None:
            print('Multidimensional WV LUT interpolation not currently supported for hyperspectral.')
            return()

        ## convolution lut and make rgi
        band_averaged = {}
        for band in rsr_bands:
            ## old LUT
            if config=='201710C':
                blut = atmos.shared.rsr_convolute_nd(lut, meta['wave'],rsr[band]['response'], rsr[band]['wave'], axis=4)
                rgi = scipy.interpolate.RegularGridInterpolator([meta['ths'], meta['thv'], meta['wv'], range(3)],blut,\
                                                                bounds_error=False, fill_value=None)
                iw = rgi((ths, thv, uwv, par_id))
            ## new LUT
            else:
                blut = atmos.shared.rsr_convolute_nd(lut, meta['wave'],rsr[band]['response'], rsr[band]['wave'], axis=2)
                ipd = {p:pi for pi, p in enumerate(meta['par'])}
                rgi = scipy.interpolate.RegularGridInterpolator([meta['pressure'], range(len(meta['par'])),
                                                                 meta['vza'], meta['sza'], meta['wv']],blut,
                                                                 bounds_error=False, fill_value=None)
                iw = rgi((pressure, ipd[par], thv, ths, uwv))

            band_averaged[band] = iw
        return(band_averaged)
