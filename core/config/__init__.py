from enum import Enum, auto

class OP_TYPE(Enum):
    S1 = auto()
    S2 = auto()
    GENERIC = auto()

s1_list = ['apply_orbit', 'calibrate', 'terrain_correction', 'thermal_noise_removal', 'topsar_deburst', 'speckle_filter']
s2_list = ['atmos']
generic = ['read', 'write', 'stack', 'subset', 'split', 'reproject', 'resample', 'convert', 'mean_denoising']

def check_op_type(op_name:str) -> OP_TYPE:
    if op_name in s1_list:
        return OP_TYPE.S1
    elif op_name in s2_list:
        return OP_TYPE.S2
    elif op_name in generic:
        return OP_TYPE.GENERIC
    else:
        raise ValueError(f'{op_name} is not a valid operation')

from .parse_error import *
from .parse_str import *
from .validate_config import *
from .parse_config import *
