DET_BANDS = ['B1', 'B2', 'B11']

S2_RES_BAND_MAP = {
    '10': 'B2',
    '20': 'B11',
    '60': 'B1'
}

ORBIT_TYPE = {
    'SENTINEL_PRECISE' : 'Sentinel Precise (Auto Download)',
    'SENTINEL_RESTITUTED': 'Sentinel Restituted (Auto Download)',
    'DORIS_POR': 'Doris Preliminary (ENVISAT)',
    'DORIS_VOR': 'Doris Precise VOR (ENVISAT) (Auto Download)',
    'DELFT_PRECISE': 'DELFT Precise (ENVISAT, ERS1&2) (Auto Download)',
    'PRARE_PRECISE': 'PRARE Precise (ERS1&2) (Auto Download)',
    'K5_PRECISE': 'Kompsat5 Precise'
}

from .gpf_const import *
from .gpf_op_params import *
from .check_size import *
from .meta_func import *
from .product_to_ds import *
from .projection_meta import *

from .gpf_meta import *

from .gpf_constructor import *
from .gpf_copy import *
from .gpf_band import *
from .gpf_read import *
from .gpf_write import *
from .gpf_s1_preprocess import *
from .gpf_dim import *
from .gpf_merge import *