from osgeo import gdal

GDAL_DTYPE_MAP = {
    'bool': gdal.GDT_Byte,
    'uint8': gdal.GDT_Byte,
    'int8': gdal.GDT_Byte,
    'uint16': gdal.GDT_UInt16,
    'int16': gdal.GDT_Int16,
    'uint32': gdal.GDT_UInt32,
    'int32': gdal.GDT_Int32,
    'uint64': gdal.GDT_UInt64,
    'int64': gdal.GDT_Int64,
    'float32': gdal.GDT_Float32,
    'float64': gdal.GDT_Float64
}

RESAMPLING_METHODS = {
    'nearest' : gdal.GRA_NearestNeighbour,
    'bilinear': gdal.GRA_Bilinear,
    'cubic': gdal.GRA_Cubic,
    'cubicspline': gdal.GRA_CubicSpline,
    'lanczos': gdal.GRA_Lanczos,
}

from .gdal_vector import *
from .gdal_file_info import *
from .check_projection import *
from .gdal_meta_from_raw import *
from .warp_to import *
from .op_funcs import *
from .gdal_funcs import *
from .gdal_read import *
from .gdal_ds import *
from .gdal_reproj import *
from .gdal_merge import *
from .projection_read import *
from .gdal_warp import *
