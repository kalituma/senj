from typing import List, AnyStr, TYPE_CHECKING

import os
from core.util.nc import read_nc

if TYPE_CHECKING:
    from netCDF4 import Dataset

def load_raster_nc(paths:List[AnyStr]) -> List["Dataset"]:

    for path in paths:
        assert os.path.splitext(path)[1] == os.path.splitext(paths[0])[1], f'All input files should have the same extension'
    return [read_nc(path) for path in paths]