from typing import List
import os

from core.util import ModuleType, ProductType
from core.util import query_dict
from core.raster import Raster
from core.raster.funcs import apply_band_names_to_snap
from core.raster.funcs.reader import BaseReader
from core.raster.funcs.read_adapter import SnapAdapter, SnapMetaBuilder, GdalAdapter
from core.raster.funcs.meta import MetaDictManager

# safe, dim
class SafeSnapReader(BaseReader, SnapAdapter):
    def __init__(self, safe_path:str):
        super().__init__()

        self.initialize_raster(safe_path, ModuleType.SNAP)
        self.set_meta_builder(SnapMetaBuilder)

        assert self.product_type == ProductType.S1 or self.product_type == ProductType.S2, 'SNAP meta builder is only supported for S1 and S2 products'

    def read(self, *args, **kwargs) -> Raster:
        self.img_paths = self.load_img_paths()
        self.raster.raw = self.load_raster(self.img_paths)
        self.raster.product_type = self.product_type

        self.meta_builder.build_meta_dict(False)
        self.raster.meta_dict = self.meta_builder.after_build()

        if self.raster.meta_dict is None:
            MetaDictManager(self.raster).update_band_mapping(self.meta_builder.btoi_from_header)
        else:
            self.raster.copy_band_map_from_meta()

        self.raster = apply_band_names_to_snap(self.raster, self.meta_builder.btoi_from_header, self.raster.meta_dict)

        return self.raster
    
class SafeGdalReader(BaseReader, GdalAdapter):
    def __init__(self, file_path: str):
        super().__init__()
        
        self.initialize_raster(file_path, ModuleType.GDAL)
        self.set_meta_builder(SnapMetaBuilder)

        assert self.product_type == ProductType.S2, 'SafeGdalReader is only supported for S2 products'

    def load_img_paths(self, stack_files:list[str]) -> List[str]:
        raster_path = self.raster.path
        s2_meta_dict = self.meta_builder.meta_dict
        granule_relative_paths = query_dict("$..IMAGE_FILE", s2_meta_dict)[0]
        
        granule_paths = [os.path.join(raster_path, f'{granule_relative_path}.jp2') for granule_relative_path in granule_relative_paths]
        filtered_granule_paths = [granule_path for granule_path in granule_paths if any(band in granule_path for band in stack_files)]

        assert len(filtered_granule_paths) > 0, f'No granule paths found for bands: {stack_files}'
        filtered_granule_paths.sort()
        return filtered_granule_paths
    
    def read(self, stack_files:list[str], *args, **kwargs) -> Raster:

        self.meta_builder.build_meta_dict(False)
        self.img_paths = self.load_img_paths(stack_files)
        self.raster.raw = self.load_raster(self.img_paths, stack=True)
        self.raster.product_type = self.product_type
        self.raster.meta_dict = self.meta_builder.after_build()

        if self.raster.meta_dict is None:
            MetaDictManager(self.raster).update_band_mapping(self.meta_builder.btoi_from_header)
        else:
            MetaDictManager(self.raster).update_band_mapping()
            # self.raster.copy_band_map_from_meta()

        return self.raster
