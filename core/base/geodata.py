# core/base/geo_data.py
from abc import ABC, abstractmethod
from typing import Union, TypeVar, Dict, Any
from pathlib import Path
        
from core.util import ModuleType

T = TypeVar('T', bound='GeoData')

class GeoData(ABC):
    
    def __init__(self, path: str = None):
        super().__init__()
        
        self._module_type: ModuleType = None
        self._path: str = path
        self._raw = None
        self._is_cached: bool = False
        
        if path and not Path(path).exists():
            raise FileNotFoundError(f'{path} does not exist')
    
    @property
    def path(self) -> str:
        return self._path
        
    @path.setter
    def path(self, path: str):
        self._path = path
    
    @property
    def raw(self):
        return self._raw
        
    @raw.setter
    def raw(self, raw):
        self._raw = raw
        
    @property
    def module_type(self) -> ModuleType:
        return self._module_type
        
    @module_type.setter
    def module_type(self, module_type):
        if isinstance(module_type, str):
            self._module_type = ModuleType.from_str(module_type)
        else:
            self._module_type = module_type
    
    @property
    @abstractmethod
    def handler(self):        
        pass
    
    @abstractmethod
    def close(self):
        pass
    
    @property
    def envelope(self):
        return self.handler.get_envelope(self.raw)

    @property
    def proj(self):
        return self.handler.proj(self.raw)