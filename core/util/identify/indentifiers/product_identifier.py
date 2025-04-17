from core.util import ProductType
from abc import ABC, abstractmethod
from typing import ClassVar, List, Type, Optional, Tuple

class ProductIdentifier(ABC):
    registry: ClassVar[List[Type['ProductIdentifier']]] = []
        
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ProductIdentifier.registry.append(cls)
    
    @classmethod
    @abstractmethod
    def can_identify(cls, src_path: str) -> bool:
        pass
    
    @classmethod
    @abstractmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        pass