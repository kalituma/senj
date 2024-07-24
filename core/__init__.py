import os, sys, platform

ENV_MAP = os.environ

uname = platform.uname()

python = {'platform':sys.platform, 'version':sys.version}
system = {'sysname': uname.system, 'release': uname.release, 'machine': uname.machine, 'version': uname.version}

code_path = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.dirname(code_path)
ENV_MAP['PROJECT_PATH'] = PROJECT_PATH

ATMOS_CONFIG = os.path.join(PROJECT_PATH, 'config', 'atmos')
SCHEMA_PATH = os.path.join(PROJECT_PATH, 'config', 'schema')
ATMOS_SCRATCH_PATH = os.path.join(PROJECT_PATH, 'atmos', 'scratch')

from core.registry import Registry, LAMBDA, PROCESSOR, OPERATIONS

from core import util
from core import lambda_funcs
from core import atmos
from core import config
from core import operations
from core import logic
