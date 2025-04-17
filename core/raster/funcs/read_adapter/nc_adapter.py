from typing import List, TYPE_CHECKING

from core.util.nc import load_raster_nc
from core.raster.funcs.read_adapter import BaseAdapter

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

class NcAdapter(BaseAdapter):
    def load_raster(self, img_paths:List[str], stack:bool=False, *args, **kwargs) -> "Dataset":
        assert len(img_paths) == 1, 'NC adapter only supports single file'
        return load_raster_nc(img_paths)[0]