from typing import List
import os

from core.util import ModuleType, ProductType
from core.util import query_dict
from core.raster import Raster
from core.raster.funcs import apply_band_names_to_snap
from core.raster.funcs.reader import BaseRasterReader
from core.raster.funcs.adapter import SnapRasterAdapter, GdalRasterAdapter
from core.raster.funcs.meta import MetaBandsManager, SnapMetaBuilder

# safe, dim, tif
class SnapReader(BaseRasterReader, SnapRasterAdapter):

    def _init_reader(self, file_path: str) -> None:
        self.initialize(file_path, ModuleType.SNAP)
        self.set_meta_builder(SnapMetaBuilder)
        assert self.product_type == ProductType.S1 or self.product_type == ProductType.S2, 'SNAP meta builder is only supported for S1 and S2 products'

    def read(self, file_path: str, *args, **kwargs) -> Raster:
        
        self._init_reader(file_path)

        self.img_paths = self.load_img_paths()
        self.raster.raw = self.read_data(self.img_paths)

        self.meta_builder.build_meta_dict(False)
        self.raster.meta_dict = self.meta_builder.after_build()
        
        MetaBandsManager(self.raster).update_band_mapping()

        self.raster = apply_band_names_to_snap(self.raster, self.meta_builder.btoi_from_header, self.raster.meta_dict)

        return self.raster
    
class SafeGdalReader(BaseRasterReader, GdalRasterAdapter):
    
    def _init_reader(self, file_path: str) -> None:

        self.initialize(file_path, ModuleType.GDAL)
        self.set_meta_builder(SnapMetaBuilder)

        assert self.product_type == ProductType.S2, 'SafeGdalReader is only supported for S2 products'

    def load_img_paths(self, contained_words:list[str]) -> List[str]:

        raster_path = self.raster.path
        s2_meta_dict = self.meta_builder.meta_dict
        granule_relative_paths = query_dict("$..IMAGE_FILE", s2_meta_dict)[0]
        
        granule_paths = [os.path.join(raster_path, f'{granule_relative_path}.jp2') for granule_relative_path in granule_relative_paths]
        filtered_granule_paths = [granule_path for granule_path in granule_paths if any(band in granule_path for band in contained_words)]

        assert len(filtered_granule_paths) > 0, f'No granule paths found for bands: {contained_words}'
        filtered_granule_paths.sort()
        return filtered_granule_paths
    
    def read(self, file_path: str, contained_words:list[str], *args, **kwargs) -> Raster:

        self._init_reader(file_path)
        
        self.meta_builder.build_meta_dict(False)
        self.img_paths = self.load_img_paths(contained_words)
        self.raster.raw = self.read_data(self.img_paths, stack=True)
        self.raster.meta_dict = self.meta_builder.after_build()

        if self.raster.meta_dict is None:
            MetaBandsManager(self.raster).update_band_mapping(self.meta_builder.btoi_from_header)
        else:
            MetaBandsManager(self.raster).update_band_mapping()
            # self.raster.copy_band_map_from_meta()

        return self.raster
