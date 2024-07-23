import os, mimetypes
import core.atmos as atmos

from core.atmos.api.cdse import query as cdse_query
from core.atmos.api.cdse import download as cdse_download
from core.atmos.api.earthexplorer import query as earth_query
from core.atmos.api.earthexplorer import download as earth_download

def inputfile_test(inputfile):


    ## check if a list of files is given
    if type(inputfile) == str:
        tmp_files = inputfile.split(',')
    elif type(inputfile) == list:
        tmp_files = inputfile
    else:
        if atmos.config['verbosity'] > 0: print('Inputfile {} not recognised'.format(inputfile))
        tmp_files = []

    ## run through files
    inputfile_list = []
    for file in tmp_files:
        if len(file) == 0: continue
        file = file.strip() ## strip spaces
        if not os.path.exists(file):
            if atmos.config['verbosity'] > 0: print('Path {} does not exist.'.format(file))
            ## try and download from CDSE or EarthExplorer
            if atmos.settings['run']['scene_download']:
                ddir = atmos.settings['run']['scene_download_directory']
                if ddir is None: ddir = atmos.settings['run']['output']
                ## finc out data source to use
                bn = os.path.basename(inputfile)
                if bn[0:3] in ['S2A', 'S2B', 'S3A', 'S3B']:
                    download_source = 'CDSE'
                elif bn[0:4] in ['LC08', 'LO08', 'LT08', 'LC09', 'LO09', 'LT09', 'LT04', 'LT05', 'LE07']:
                    download_source = 'EarthExplorer'
                elif 'ECOSTRESS' in bn:
                    download_source = 'EarthExplorer'
                else:
                    print('Could not identify download source for scene {}'.format(file))
                    continue

                if atmos.config['verbosity'] > 0: print('Attempting download of scene {} from {}.'.format(file, download_source))
                if atmos.config['verbosity'] > 0: print('Querying {}'.format(download_source))

                ## Copernicus Data Space Ecosystem
                if download_source == 'CDSE':
                    urls, scenes = cdse_query(scene=bn)
                    if atmos.config['verbosity'] > 0: print('Downloading from {}'.format(download_source))
                    local_scenes = cdse_download(urls, output = ddir, verbosity = atmos.config['verbosity'])
                ## EarthExplorer
                if download_source == 'EarthExplorer':
                    entity_list, identifier_list, dataset_list = earth_query(scene=bn)
                    if atmos.config['verbosity'] > 0: print('Downloading from {}'.format(download_source))
                    local_scenes = earth_download(entity_list, dataset_list, identifier_list, output = ddir, verbosity = atmos.config['verbosity'])

                if len(local_scenes) == 1:  file = '{}'.format(local_scenes[0])
                if not os.path.exists(file): continue
            else:
                continue

        ##  remove trailing slash
        if file[-1] == os.sep: file = file[0:-1]

        if os.path.isdir(file):
            inputfile_list.append(file)
        else:
            mime = mimetypes.guess_type(file)
            if mime[0] != 'text/plain':
                if os.path.exists(file): inputfile_list.append(file) ## assume we can process this file
                continue
            with open(file, 'r') as f:
                for l in f.readlines():
                    l = l.strip()
                    if len(l) == 0: continue
                    cfiles = []
                    for fn in l.split(','):
                        fn = fn.strip()
                        if fn[-1] == os.sep: fn = fn[0:-1]
                        if os.path.exists(fn):
                            cfiles.append(fn)
                        else:
                            if atmos.config['verbosity'] > 0: print('Path {} does not exist.'.format(fn))
                    if len(cfiles)>0: inputfile_list += cfiles
    return(inputfile_list)
