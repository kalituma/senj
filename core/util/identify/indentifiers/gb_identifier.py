from pathlib import Path
from typing import Optional, Tuple

from core.util import ProductType
from core.util.identify import identify_gb
from core.util.identify.indentifiers import ProductIdentifier
class GBIdentifier(ProductIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:
        return src_path.lower().endswith('.gb2')
    
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_gb(src_path)


