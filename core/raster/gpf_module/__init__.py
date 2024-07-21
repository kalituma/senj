DET_BANDS = ['B1', 'B2', 'B11']

S2_RES_BAND_MAP = {
    '10': 'B2',
    '20': 'B11',
    '60': 'B1'
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