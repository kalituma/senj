from typing import List, TYPE_CHECKING, Tuple
from osgeo import gdal

from core.util.gdal import mosaic_by_file_paths, load_raster_gdal, merge
from core.raster.funcs.read_adapter.base_adapter import BaseAdapter

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

class GdalAdapter(BaseAdapter):
    def load_raster(self, img_paths:List[str], stack:bool=False, *args, **kwargs) -> "Dataset":
        if len(img_paths) == 1:
            self.update_meta_bounds = False
            return load_raster_gdal(img_paths)[0]
        else:
            if stack:
                self.update_meta_bounds = False
                return merge(load_raster_gdal(img_paths))
            else:
                self.update_meta_bounds = True
                return mosaic_by_file_paths(img_paths)