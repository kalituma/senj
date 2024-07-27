
from core.raster import RasterType

MODULE_EXT_MAP = {
    RasterType.GDAL : ['tif'],
    RasterType.SNAP : ['dim', 'tif', 'safe']
}

#io
READ_OP = 'read'
WRITE_OP = 'write'
MULTI_WRITE_OP = 'multi_write'

#dim
STACK_OP = 'stack'
SUBSET_OP = 'subset'
SPLIT_OP = 'split'

#pixel-wise
REPROJECT_OP = 'reproject'
RESAMPLE_OP = 'resample'
CONVERT_OP = 'convert'

#s1, snap
APPLYORBIT_OP = 'apply_orbit'
CALIBRATE_OP = 'calibrate'
TERR_CORR_OP = 'range_doppler_terrain_correction'
THERM_NOISE_OP = 'thermal_noise_removal'
TOPSAR_DEBURST_OP = 'topsar_deburst'
SPECKLE_FILTER_OP = 'speckle_filter.yaml'

#cached
ATMOSCORR_OP = 'atmos'
NL_DENOISING_OP = 'nl_mean_denoising'

from .ops import *
from .read_op import *
from .write_op import *
from .multi_write_op import *
from .subset_op import *
from .stack_op import *
from .split_op import *
from .convert_op import *

from .s1 import *
from .cached import *