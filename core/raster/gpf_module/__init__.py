from enum import Enum

DET_BANDS = ['B1', 'B2', 'B11']

S2_RES_BAND_MAP = {
    '10': 'B2',
    '20': 'B11',
    '60': 'B1'
}

class InterpolType(Enum):
    NEAREST_NEIGHBOUR = "NEAREST_NEIGHBOUR"
    BILINEAR_INTERPOLATION = "BILINEAR_INTERPOLATION"
    CUBIC_CONVOLUTION = "CUBIC_CONVOLUTION"
    BISINC_5_POINT_INTERPOLATION = "BISINC_5_POINT_INTERPOLATION"
    BISINC_11_POINT_INTERPOLATION = "BISINC_11_POINT_INTERPOLATION"
    BISINC_21_POINT_INTERPOLATION = "BISINC_21_POINT_INTERPOLATION"
    BICUBIC_INTERPOLATION = "BICUBIC_INTERPOLATION"

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value:str):
        for interp_type in cls:
            if interp_type.value == value:
                return interp_type
        return None

class DemType(Enum):
    COPERNICUS_30 = "Copernicus 30m Global DEM"
    COPERNICUS_90 = "Copernicus 90m Global DEM"
    SRTM_3SEC = "SRTM 3Sec"
    SRTM_1SEC_HGT = "SRTM 1Sec HGT"
    SRTM_1SEC_GRD = "SRTM 1Sec Grid"
    ASTER_1SEC = "ASTER 1Sec GDEM"
    ACE30 = "ACE30"
    ACE2_5 = "ACE2_5Min"
    GETASSE30 = "GETASSE30"

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value:str):
        for interp_type in cls:
            if interp_type.value == value:
                return interp_type
        return None
class ORBIT_TYPE(Enum):
    SENTINEL_PRECISE = 'Sentinel Precise (Auto Download)'
    SENTINEL_RESTITUTED = 'Sentinel Restituted (Auto Download)'
    DORIS_POR = 'DORIS Preliminary POR (ENVISAT)'
    DORIS_VOR = 'DORIS Precise VOR (ENVISAT) (Auto Download)'
    DELFT_PRECISE = 'DELFT Precise (ENVISAT, ERS1&2) (Auto Download)'
    PRARE_PRECISE = 'PRARE Precise (ERS1&2) (Auto Download)'
    K5_PRECISE = 'Kompsat5 Precise'

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value:str):
        for orbit_type in cls:
            if orbit_type.value == value:
                return orbit_type
        return None

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