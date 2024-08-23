from core.raster import RasterType

MODULE_EXT_MAP = {
    RasterType.GDAL : ['tif', 'xml'],
    RasterType.SNAP : ['dim', 'tif', 'safe', 'xml']
}

from core.util.op.op_const import *
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