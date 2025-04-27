from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Type, TYPE_CHECKING
from pathlib import Path

from core.util.identify import identify_product
from core.raster import Raster, ModuleType, ProductType
from core.raster.funcs.load_image_paths import load_images_paths

if TYPE_CHECKING:
    from core.raster.funcs.meta import MetaBuilder

class BaseRasterReader(ABC):
    def __init__(self):
        self._raster: Optional[Raster] = None
        self._module_type: Optional[ModuleType] = None
        self._product_type: Optional[ProductType] = None        
        self._meta_builder: Optional["MetaBuilder"] = None
        self._img_paths: Optional[List[str]] = None


    @property
    def raster(self) -> Raster:
        if self._raster is None:
            raise ValueError("Raster object is not initialized")
        return self._raster    

    @raster.setter
    def raster(self, value: Raster) -> None:
        self._raster = value

    @property
    def module_type(self) -> ModuleType:
        if self._module_type is None:
            raise ValueError("Module type is not initialized")
        return self._module_type
    
    @module_type.setter
    def module_type(self, value: ModuleType) -> None:
        self._module_type = value
        if self._raster is not None:
            self._raster.module_type = value
    
    @property
    def product_type(self) -> ProductType:
        if self._product_type is None:
            raise ValueError("Product type is not initialized")
        return self._product_type
    
    @product_type.setter
    def product_type(self, value: ProductType) -> None:
        self._product_type = value
        if self._raster is not None:
            self._raster.product_type = value
    
    @property
    def meta_builder(self) -> "MetaBuilder":
        if self._meta_builder is None:
            raise ValueError("Meta builder is not initialized")
        return self._meta_builder
    
    @property
    def img_paths(self) -> List[str]:
        if self._img_paths is None:
            raise ValueError("Image paths are not initialized")
        return self._img_paths
    
    @img_paths.setter
    def img_paths(self, value: List[str]) -> None:
        self._img_paths = value
        
    def set_meta_builder(self, builder_class: Type["MetaBuilder"]) -> None:
        self._meta_builder = builder_class(self)

    def initialize(self, file_path: str, module_type: ModuleType) -> None:
        self._raster = Raster.create(file_path, module_type)
        self.module_type = module_type
        self.product_type, _meta_path = identify_product(file_path)

        if self._product_type == ProductType.WV and Path(_meta_path).suffix.lower() == '.xml':
            self._raster.path = _meta_path        
        
    def load_img_paths(self, *args, **kwargs) -> List[str]:
        return load_images_paths(self._raster.path, self._product_type, self._module_type)

    @abstractmethod
    def read(self, file_path:str, *args, **kwargs) -> Raster:
        pass