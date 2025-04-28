from abc import ABC, abstractmethod
from typing import Optional

from core.vector import Vector
from core.util import ModuleType

class BaseVectorReader(ABC):
    def __init__(self, *args, **kwargs):
        self._vector: Optional[Vector] = None
        self._module_type: Optional[ModuleType] = None        
        self._path: Optional[str] = None
    
    @property
    def vector(self) -> Optional[Vector]:
        return self._vector
    
    @vector.setter
    def vector(self, value: Vector):
        self._vector = value
    
    @property
    def module_type(self) -> Optional[ModuleType]:
        return self._module_type
    
    @module_type.setter
    def module_type(self, value: ModuleType):
        self._module_type = value
        
    @property
    def path(self) -> Optional[str]:
        return self._path
    
    @path.setter
    def path(self, value: str):
        self._path = value

    def initialize(self, file_path: str, module_type: ModuleType):
        self.vector = Vector.create(file_path, module_type)
        self.module_type = module_type

    @abstractmethod
    def read(self, file_path: str, *args, **kwargs):
        pass
