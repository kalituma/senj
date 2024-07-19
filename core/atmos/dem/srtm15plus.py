import os
from core import atmos
def srtm15plus(path=None):

    url = 'https://topex.ucsd.edu/pub/srtm15_plus/SRTM15_V2.3.nc'
    if path is not None:
        local_file = path
    else:
        local_file = '{}/{}'.format(atmos.config['external_dir'], 'SRTM15_V2.3.nc')
    local_dir = os.path.dirname(local_file)

    ## download/extract
    if not os.path.exists(local_file):
        print('Downloading {} (6.5GB)'.format(local_file))
        ret = atmos.shared.download_file(url, local_file, verify_ssl=False)

    ## return local path
    if os.path.exists(local_file):
        return(local_file)
    else:
        return(None)
