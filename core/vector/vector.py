from typing import Union, TypeVar, Dict, List, Any, TYPE_CHECKING, Optional
from pathlib import Path

from core.base import GeoData
from core.util import ModuleType
from core.vector.handler import GdalVectorHandler

if TYPE_CHECKING:
    from core.vector.handler import VectorHandler

T = TypeVar('T', bound='Vector')

class Vector(GeoData):    
    
    _module_handlers: Dict[ModuleType, "VectorHandler"] = {
        ModuleType.GDAL: GdalVectorHandler(),
    }
    
    def __init__(self, path: str = None):
        super().__init__(path)
        
        self._features_data: Dict = None
        self._geometry_type: str = None
        self._fields: List[Dict] = None
        
    @property
    def handler(self):
        if not self.module_type:
            raise ValueError('Module type is not set')
        
        if self.module_type not in self._module_handlers:
            raise ValueError(f'Module type {self.module_type} is not supported')
            
        return self._module_handlers[self.module_type]
    
    @staticmethod
    def from_vector(vector: T, **kwargs):
        new_vector = Vector(vector.path)
        
        for key, value in vars(vector).items():
            if key in ['op_history', '_module_type', '_path']:
                setattr(new_vector, key, value)
        
        for key, value in kwargs.items():
            setattr(new_vector, key, value)
            
        return new_vector
    
    @classmethod
    def create(cls, path: str, module_type: Optional[ModuleType]=None, **kwargs):
        vector = cls(path)
        
        if module_type:
            vector.module_type = module_type        
        
        return vector
    
    
    @property
    def features(self) -> Dict:
        if not self._features_data and self.raw:
            self._features_data = self.handler.get_features(self.raw)
        return self._features_data
        
    @features.setter
    def features(self, features: Dict):
        self._features_data = features
    
    @property
    def geometry_type(self) -> str:        
        if not self._geometry_type and self.raw:
            self._geometry_type = self.handler.get_geometry_type(self.raw)
        return self._geometry_type
    
    @property
    def fields(self) -> List[Dict]:        
        if not self._fields and self.raw:
            self._fields = self.handler.get_fields(self.raw)
        return self._fields
    
    def get_feature_count(self) -> int:
        return self.handler.get_feature_count(self.raw)
    
    def get_layer_names(self) -> List[str]:
        return self.handler.get_layer_names(self.raw)
    
    def __len__(self):
        return self.get_feature_count()
    
    def __str__(self):
        return f'Vector: {self.path} ({self.geometry_type}) with {len(self)} features'
