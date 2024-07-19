import os
from osgeo import gdal, gdalconst
from core import atmos

def copernicus_dem_rpc(dct_limit, output=None):

    if gdal.__version__ < '3.3':
        from osgeo.utils import gdal_merge
    else:
        from osgeo_utils import gdal_merge

    if output == None: output = '{}'.format(atmos.config['scratch_dir'])
    pos = dct_limit['p']((dct_limit['xrange'][0],dct_limit['xrange'][0],\
                          dct_limit['xrange'][1],dct_limit['xrange'][1]),\
                         (dct_limit['yrange'][0],dct_limit['yrange'][1],\
                          dct_limit['yrange'][0],dct_limit['yrange'][1]), inverse=True)
    pos_limit = [min(pos[1]), min(pos[0]), max(pos[1]), max(pos[0])]
    dem_files = atmos.dem.copernicus_dem_find(pos_limit)

    if len(dem_files) == 1:
        rpc_dem = dem_files[0]
    elif len(dem_files) > 1:
        rpc_dem =f'{output}/dem_merged.tif'
        if os.path.exists(rpc_dem): os.remove(rpc_dem)
        print(f'Merging {len(dem_files)} tiles to {rpc_dem}')
        #gdal_merge.main(['', '-o', rpc_dem, '-n', '0']+dem_files)
        cwd = os.getcwd()
        odir = os.path.dirname(rpc_dem)
        os.chdir(odir)
        gdal_merge.main(['', '-quiet', '-n', '0']+dem_files) ## calling without -o will generate out.tif in cwd
        if os.path.exists('out.tif'): os.rename('out.tif', os.path.basename(rpc_dem))
        os.chdir(cwd)
    return(rpc_dem)
