from pathlib import Path
from typing import Optional, Tuple

from core.util import ProductType
from core.util.identify import identify_safe, identify_dim
from core.util.identify.indentifiers import ProductIdentifier

class SafeIdentifier(ProductIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:        
        return src_path.lower().endswith('.safe')
        
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_safe(src_path)

class DimIdentifier(ProductIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:
        return src_path.lower().endswith('.dim') or src_path.lower().endswith('.data')
        
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_dim(src_path)