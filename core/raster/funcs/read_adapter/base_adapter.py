from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

class BaseAdapter(ABC):
    @property
    def update_meta_bounds(self) -> bool:
        return self._update_meta_bounds
    
    @update_meta_bounds.setter
    def update_meta_bounds(self, value: bool):
        self._update_meta_bounds = value

    @abstractmethod
    def load_raster(self, img_paths:List[str], *args, **kwargs) -> "Dataset":
        pass