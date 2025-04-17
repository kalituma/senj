from pathlib import Path
from typing import Optional, Tuple

from core.util import ProductType
from core.util.identify import identify_nc
from core.util.identify.indentifiers import ProductIdentifier

class NcIdentifier(ProductIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:
        return src_path.lower().endswith('.nc') or src_path.lower().endswith('.nc4')
    
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_nc(src_path)