import os
from core import atmos

def load(settings):

    ## read defaults
    default_settings = os.path.join(atmos.ATMOS_CONFIG, 'defaults.txt')
    setd = atmos.setting.read(default_settings)

    ## read settings file
    if settings is not None:
        ## path to settings file given
        if type(settings) is str:
            setf = os.path.join(atmos.ATMOS_CONFIG, 'defaults', f'{settings}.txt')
            if (os.path.exists(settings)) and (not os.path.isdir(settings)):
                setu = atmos.setting.read(settings)
            elif os.path.exists(setf):
                setu = atmos.setting.read(setf)
            else:
                print('Settings file {} not found.'.format(settings))
                setu = setd
        elif type(settings) is dict:
            setu = settings
        else:
            print('Settings not recognised.')
            setu = setd
    else: setu={}

    ## set defaults for options not specified
    for key in setd.keys():
        if key in setu.keys(): continue
        else: setu[key] = setd[key]
    return(setu)
