## def acolite_settings
##
##
## Written by Quinten Vanhellemont 2017-11-30
## Last modifications:
##                2018-07-18 (QV) changed acolite import name

import os
import core.atmos as atmos
from core.atmos.setting.read import read

def load(settings):

    ## read defaults
    default_settings = os.path.join(atmos.ATMOS_CONFIG, 'defaults.txt')
    setd = read(default_settings)

    ## read settings file
    if settings is not None:
        ## path to settings file given
        if type(settings) is str:
            setf = os.path.join(atmos.ATMOS_CONFIG, 'defaults', f'{settings}.txt')
            if (os.path.exists(settings)) and (not os.path.isdir(settings)):
                setu = read(settings)
            elif os.path.exists(setf):
                setu = read(setf)
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
