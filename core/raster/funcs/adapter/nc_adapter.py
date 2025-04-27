from typing import List, TYPE_CHECKING

from core.util.nc import load_raster_nc
from core.raster.funcs.adapter import BaseRasterAdapter

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

class NcRasterAdapter(BaseRasterAdapter):

    def read_data(self, img_paths:List[str], stack:bool=False, *args, **kwargs) -> "Dataset":
        assert len(img_paths) == 1, 'NC adapter only supports single file'
        return load_raster_nc(img_paths)[0]

    def write_data(self, raster, out_path:str, *args, **kwargs):
        raise NotImplementedError("Writing NetCDF files is not implemented in this adapter.")