from typing import List
import os
from core.util import ModuleType, ProductType
from core.util import query_dict
from core.raster import Raster
from core.raster.funcs.reader import BaseRasterReader
from core.raster.funcs.adapter import GdalRasterAdapter
from core.raster.funcs.meta import MetaBandsManager, TifMetaBuilder, GribMetaBuilder
# tif
class TifGdalReader(BaseRasterReader, GdalRasterAdapter):

    def _init_reader(self, file_path: str) -> None:
        self.initialize(file_path, ModuleType.GDAL)
        self.set_meta_builder(TifMetaBuilder)

    def read(self, file_path:str, *args, **kwargs) -> Raster:

        self._init_reader(file_path)

        self.img_paths = self.load_img_paths()
        self.raster.raw = self.read_data(self.img_paths)

        self.meta_builder.build_meta_dict(self.update_meta_bounds)
        self.raster.meta_dict = self.meta_builder.after_build()

        MetaBandsManager(self.raster).update_band_mapping(self.meta_builder.btoi_from_header)

        return self.raster

class GribGdalReader(BaseRasterReader, GdalRasterAdapter):

    def _init_reader(self, file_path: str) -> None:
        self.initialize(file_path, ModuleType.GDAL)
        self.set_meta_builder(GribMetaBuilder)
    
    def read(self, file_path:str, *args, **kwargs) -> Raster:

        self._init_reader(file_path)

        self.img_paths = self.load_img_paths()
        self.raster.raw = self.read_data(self.img_paths)

        self.meta_builder.build_meta_dict(self.update_meta_bounds)
        self.raster.meta_dict = self.meta_builder.after_build()
                
        MetaBandsManager(self.raster).update_band_mapping()

        return self.raster