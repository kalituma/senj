from typing import List
import os
from core.util import ModuleType, ProductType
from core.util import query_dict
from core.raster import Raster
from core.raster.funcs.reader import BaseReader
from core.raster.funcs.read_adapter import GdalAdapter, TifMetaBuilder, GribMetaBuilder

# tif
class TifGdalReader(BaseReader, GdalAdapter):
    def __init__(self, file_path: str):
        super().__init__()
        
        self.initialize_raster(file_path, ModuleType.GDAL)
        self.set_meta_builder(TifMetaBuilder)

    def read(self, *args, **kwargs) -> Raster:
        
        self.img_paths = self.load_img_paths()
        self.raster.raw = self.load_raster(self.img_paths)
        self.raster.product_type = self.product_type

        self.meta_builder.build_meta_dict(self.update_meta_bounds)
        self.raster.meta_dict = self.meta_builder.after_build()

        if self.raster.meta_dict is None:
            self.raster.update_index_bnames(self.meta_builder.btoi_from_header)
        else:
            self.raster.copy_band_map_from_meta()

        return self.raster

class GribGdalReader(BaseReader, GdalAdapter):
    def __init__(self, file_path: str):
        super().__init__()
        
        self.initialize_raster(file_path, ModuleType.GDAL)
        self.set_meta_builder(GribMetaBuilder)
    
    def read(self, *args, **kwargs) -> Raster:
        self.img_paths = self.load_img_paths()
        self.raster.raw = self.load_raster(self.img_paths)
        self.raster.product_type = self.product_type

        self.meta_builder.build_meta_dict(self.update_meta_bounds)
        self.raster.meta_dict = self.meta_builder.after_build()

        if self.raster.meta_dict is None:
            self.raster.update_index_bnames(self.meta_builder.btoi_from_header)
        else:
            self.raster.copy_band_map_from_meta()

        return self.raster