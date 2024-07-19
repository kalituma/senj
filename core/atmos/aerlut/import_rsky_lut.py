import os
import numpy as np
import scipy.interpolate
from core import atmos

def import_rsky_lut(model, lutbase='ACOLITE-RSKY-202102-82W', sensor=None, override=False,
                    get_remote = True, remote_base = None):

    ## use URL from main config
    if remote_base is None: remote_base = '{}'.format(atmos.config['lut_url'])

    if True:
            lutdir = '{}/{}/'.format(atmos.config['lut_dir'], '-'.join(lutbase.split('-')[1:3]))
            lutnc = '{}/{}-MOD{}.nc'.format(lutdir, lutbase, model)

            ## base lut
            if sensor is None:
                ## extract bz2 files
                unzipped = False
                lutncbz2 = '{}.bz2'.format(lutnc)

                ## try downloading LUT from GitHub
                if (not os.path.isfile(lutnc)) & (not os.path.isfile(lutncbz2)) & (get_remote):
                    remote_lut = '{}/{}/{}'.format(remote_base, '-'.join(lutbase.split('-')[1:3]), os.path.basename(lutncbz2))
                    try:
                        atmos.shared.download_file(remote_lut, lutncbz2)
                    except:
                        print('Could not download remote lut {} to {}'.format(remote_lut, lutncbz2))

                ## extract bz LUT
                if (not os.path.isfile(lutnc)) & (os.path.isfile(lutncbz2)):
                    import bz2, shutil
                    with bz2.BZ2File(lutncbz2) as fi, open(lutnc,"wb") as fo:
                        shutil.copyfileobj(fi,fo)
                    unzipped = True
                ## end extract bz2 files

                ## read LUT
                lut, meta = atmos.shared.lutnc_import(lutnc)
                lut = np.flip(lut, axis=1) ## flip raa
                if unzipped: os.remove(lutnc) ## clear unzipped LUT

                dim = [meta['wave'], meta['azi'], meta['thv'], meta['ths'], meta['tau']]
                #if 'press' in meta:
                #    if type(meta['press']) is np.ndarray:
                #        dim = [meta['press'], meta['wave'], meta['azi'], meta['thv'], meta['ths'], meta['tau']]
                if 'wind' in meta:
                    if type(meta['wind']) is np.ndarray:
                        dim = [meta['wave'], meta['azi'], meta['thv'], meta['ths'], meta['wind'], meta['tau']]

                rgi = scipy.interpolate.RegularGridInterpolator(dim, lut, bounds_error=False, fill_value=np.nan)
                return(lut, meta, dim, rgi)
            ## sensor specific lut
            else:
                #lutnc_s = '{}/{}/{}-MOD{}_{}.nc'.format(lutdir, sensor, lutbase, model, sensor)
                slut = '{}-MOD{}_{}'.format(lutbase, model, sensor)
                lutnc_s = '{}/{}/{}.nc'.format(lutdir, sensor, slut)

                ## get sensor RSR
                lutdir=atmos.config['lut_dir']
                rsr_file = atmos.config['data_dir']+'/RSR/'+sensor+'.txt'
                rsr, rsr_bands = core.util.rsr_read(file=rsr_file)

                ## make new sensor lutfile
                if (override) & (os.path.isfile(lutnc_s)): os.remove(lutnc_s)

                ## try downloading LUT from GitHub
                if (not os.path.isfile(lutnc_s)) & (get_remote):
                    remote_lut = '{}/{}/{}/{}.nc'.format(remote_base, '-'.join(lutbase.split('-')[1:3]), sensor, slut)
                    try:
                        atmos.shared.download_file(remote_lut, lutnc_s)
                    except:
                        print('Could not download remote lut {} to {}'.format(remote_lut, lutnc_s))

                ## generate LUT if download did not work
                if not os.path.isfile(lutnc_s):
                    print('Resampling RSKY LUT {} to {}'.format(os.path.basename(lutnc), sensor))
                    if not os.path.exists(os.path.dirname(lutnc_s)): os.makedirs(os.path.dirname(lutnc_s))
                    ## read lut
                    lut, meta, dim, rgi = atmos.aerlut.import_rsky_lut(model, lutbase=lutbase)
                    ## resample to bands
                    lut_sensor = {}
                    for band in rsr_bands:
                        lut_sensor[band] = atmos.shared.rsr_convolute_nd(lut, meta['wave'],rsr[band]['response'], rsr[band]['wave'], axis=0)
                    #return(lut_sensor, meta, dim)
                    ## save to new file
                    from netCDF4 import Dataset
                    nc = Dataset(lutnc_s, 'w', format='NETCDF4_CLASSIC')
                    for i in meta.keys():
                        attdata=meta[i]
                        if isinstance(attdata,list):
                            if isinstance(attdata[0],str):
                                attdata=','.join(attdata)
                        setattr(nc, i, attdata)
                    nc.createDimension('azi', len(dim[1]))
                    nc.createDimension('thv', len(dim[2]))
                    nc.createDimension('ths', len(dim[3]))
                    nc.createDimension('wind', len(dim[4]))
                    nc.createDimension('tau', len(dim[5]))
                    ## write LUT
                    for band in rsr_bands:
                        var = nc.createVariable(band,np.float32,('azi','thv','ths','wind', 'tau'))
                        nc.variables[band][:] = lut_sensor[band].astype(np.float32)
                    nc.close()
                ## end resample lut

                ## lutfile was already resampled
                if os.path.isfile(lutnc_s):
                    lut_sensor, meta = atmos.shared.lutnc_import(lutnc_s)
                    ## workaround for old LUTs which had no wind speed dimension
                    if 'wind' not in meta:
                        dim = [meta['azi'], meta['thv'], meta['ths'], meta['tau']]
                    else:
                        dim = [meta['azi'], meta['thv'], meta['ths'], meta['wind'], meta['tau']]
                    rgi_sensor = {}
                    for band in rsr_bands:
                        rgi_sensor[band] = scipy.interpolate.RegularGridInterpolator(dim, lut_sensor[band], bounds_error=False, fill_value=np.nan)
                    return(lut_sensor, meta, dim, rgi_sensor)
