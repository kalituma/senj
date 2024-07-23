OUT_TYPE_MAP = {
    'tif': 'GeoTIFF',
    'bigtif': 'GeoTIFF-BigTIFF',
    'dim': 'BEAM-DIMAP'
}

EXT_MAP = {
    'gdal': 'tif',
    'snap': ['dim', 'tif']
}



from .raster_type import *
from .raster import *

from .funcs import *
