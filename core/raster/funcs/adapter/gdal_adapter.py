from typing import List, TYPE_CHECKING, Tuple
from pathlib import Path

from core.util.gdal import mosaic_by_file_paths, load_raster_gdal, merge, copy_ds

from core.raster.funcs.adapter.base_raster_adapter import BaseRasterAdapter

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

ALLOWED_EXTENSIONS = [ '.tif']
class GdalRasterAdapter(BaseRasterAdapter):

    def read_data(self, img_paths:List[str], stack:bool=False, *args, **kwargs) -> "Dataset":
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
    
    def write_data(self, ds: "Dataset", out_path:str, is_bigtiff:bool, compress:bool, *args, **kwargs):
        
        assert Path(out_path).suffix.lower() in ALLOWED_EXTENSIONS

        return copy_ds(ds, 'GTiff', is_bigtiff=is_bigtiff, compress=compress,out_path=out_path)