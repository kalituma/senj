import os, sys, platform

ENV_MAP = os.environ

def initialize():

    uname = platform.uname()

    python = {'platform':sys.platform, 'version':sys.version}
    system = {'sysname': uname.system, 'release': uname.release, 'machine': uname.machine, 'version': uname.version}

    global PROJECT_PATH
    PROJECT_PATH = ENV_MAP.get('PROJECT_PATH')

    if not PROJECT_PATH:
        raise Exception('PROJECT_PATH not set in environment')

    global ATMOS_CONFIG, SCHEMA_PATH, ATMOS_SCRATCH_PATH

    ATMOS_CONFIG = os.path.join(PROJECT_PATH, 'config', 'atmos')
    SCHEMA_PATH = os.path.join(PROJECT_PATH, 'config', 'schema')
    ATMOS_SCRATCH_PATH = os.path.join(PROJECT_PATH, 'atmos', 'scratch')

initialize()

# not importing snap
from core.registry import Registry, LAMBDA, PROCESSOR, OPERATIONS
from core import util
from core import graph
from core import lambda_funcs
from core import atmos
from core import logic

# importing snap
from core import operations
from core import config

