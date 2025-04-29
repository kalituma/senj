from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from core.util import ModuleType

if TYPE_CHECKING:
    from core.vector import Vector

class BaseVectorWriter(ABC):
    def __init__(self, *args, **kwargs):
        self._vector: Optional[Vector] = None
        self._module_type: Optional[ModuleType] = None

    @property
    def vector(self):
        return self._vector
    
    @vector.setter
    def vector(self, vector: "Vector"):
        self._vector = vector

    @property
    def module_type(self):
        return self._module_type
    
    @module_type.setter
    def module_type(self, module_type: ModuleType):
        self._module_type = module_type    

    @abstractmethod
    def write(self, file_path: str, vector: "Vector", *args, **kwargs) -> None:
        pass