import os, sys, platform

import core
from core import PROJECT_PATH, ATMOS_CONFIG, code_path

from core.atmos import shared
from core.atmos import ac
from core.atmos import atmosp
from core.atmos import dem
from core.atmos.setting import parse, load
from core.atmos import aerlut
from core.atmos import parameters

if not os.path.exists(ATMOS_CONFIG):
    range_level = 0
    for i in range(range_level):
        PROJECT_PATH = os.path.split(PROJECT_PATH)[0]

cfile = os.path.join(ATMOS_CONFIG, 'config.txt')
config = shared.import_config(cfile)

config['code_path'] = code_path
config['path'] = PROJECT_PATH

for t in config:
    ## set EARTHDATA credentials
    if t in ['EARTHDATA_u', 'EARTHDATA_p']:
        if (t not in os.environ) & (len(config[t]) > 0): os.environ[t] = config[t]
        continue
    ## split lists (currently only sensors)
    if ',' in config[t]:
        config[t] = config[t].split(',')
        continue

    ## test paths
    ## replace $ACDIR in config by ac.path
    if '$ACDIR' == config[t][0:6]:
        # os.path.join did not give the intended result on Windows
        config[t] = PROJECT_PATH + '/' + config[t].replace('$ACDIR', '')
        config[t] = config[t].replace('/', os.sep)

        ## make acolite dirs if they do not exist
        if not (os.path.exists(config[t])):
            os.makedirs(config[t])

    if (os.path.exists(config[t])):
        config[t] = os.path.abspath(config[t])

param = {'scaling': atmosp.parameter_scaling(), 'discretisation': atmosp.parameter_discretisation()}
import json
with open(config['parameter_cf_attributes'], 'r', encoding='utf-8') as f:
    param['attributes'] = json.load(f)

settings = {}
## read default processing settings
settings['defaults'] = parse(None, settings=load(None), merge=False)
## copy defaults to run, run will be updated with user settings and sensor defaults
settings['run'] = {k:settings['defaults'][k] for k in settings['defaults']}

