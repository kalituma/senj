## def hgt_download
## download DEM HGT SRTM files
## written by Quinten Vanhellemont, RBINS
## 2021-04-21
## modifications: 2022-01-01 (QV) check if retrieved zipfile is valid
##                2022-07-06 (QV) check if file exists before deleting
##                2022-07-07 (QV) added SRTM1 DEM

import zipfile, os
from core import atmos

def hgt_download(tile, url_base, hgt_dir = None, override = False):

    if hgt_dir is None: hgt_dir = atmos.config['hgt_dir']
    if not os.path.exists(hgt_dir): os.makedirs(hgt_dir)

    f_url = url_base.format(tile)
    f_local = f'{hgt_dir}/{os.path.basename(f_url)}'

    print(f_url)
    print(f_local)

    if not os.path.exists(f_local):
        try:
            ret = atmos.shared.download_file(f_url, f_local)
            if os.path.exists(f_local):
                print('Downloaded {}'.format(f_local))
        except BaseException as err:
            print("Download error {}, {}".format(err, type(err)))
            print('Downloading {} failed'.format(f_local))
            pass

    ## test file
    try:
        zfile = f'{os.path.basename(f_local).split(".")[0]}.hgt'
        with zipfile.ZipFile(f_local, mode='r') as f:
            data_read = f.read(zfile)
    except:
        if os.path.exists(f_local):
            print('SRTM DEM: {} not a zipfile'.format(f_local))
            print('SRTM DEM: Likely incomplete download. Removing {}'.format(f_local))
            os.remove(f_local)
        else:
            print('SRTM DEM: {} does not exist'.format(f_local))

    if os.path.exists(f_local):
        return(f_local)
    else:
        return()
