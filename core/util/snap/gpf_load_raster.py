import os
from typing import List, AnyStr
from esa_snappy import Product
from core.util.snap import read_gpf

def load_raster_gpf(paths:List[AnyStr]) -> List[Product]:

    for path in paths:
        assert os.path.splitext(path)[1] == os.path.splitext(paths[0])[1], f'All input files should have the same extension'
    return [read_gpf(path) for path in paths]