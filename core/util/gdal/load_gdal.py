import os
from osgeo.gdal import Dataset
from core.util.gdal import read_tif

def load_raster_gdal(paths:list[str]) -> list[Dataset]:

    for path in paths:
        assert os.path.splitext(path)[1] == os.path.splitext(paths[0])[1], f'All input files should have the same extension'
    return [read_tif(path) for path in paths]