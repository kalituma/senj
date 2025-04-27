from typing import List, TYPE_CHECKING
from abc import ABC, abstractmethod
from core.base.adapter import BaseAdapter
if TYPE_CHECKING:
    from osgeo.gdal import Dataset

class BaseRasterAdapter(BaseAdapter):
    @property
    def update_meta_bounds(self) -> bool:
        return self._update_meta_bounds
    
    @update_meta_bounds.setter
    def update_meta_bounds(self, value: bool):
        self._update_meta_bounds = value