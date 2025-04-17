from pathlib import Path
from typing import Optional, Tuple

from core.util import ProductType
from core.util.identify import identify_wv, identify_capella, identify_ps, identify_cas500, identify_k3
from core.util.identify.indentifiers import ProductIdentifier

class TifIdentifier(ProductIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:
        return src_path.lower().endswith('.tif')       

    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        raise NotImplementedError("TifIdentifier is not implemented")

class WVIdentifier(TifIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:
        return super().can_identify(src_path) or src_path.lower().endswith('.xml')
    
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_wv(src_path)

class CapellaIdentifier(TifIdentifier):
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_capella(src_path)

class CasIdentifier(TifIdentifier):
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_cas500(src_path)

class K3Identifier(TifIdentifier):
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_k3(src_path)

class PSIdentifier(TifIdentifier):
    @classmethod
    def can_identify(cls, src_path: str) -> bool:
        return super().can_identify(src_path) or src_path.lower().endswith('.xml') or src_path.lower().endswith('.json')
    
    @classmethod
    def identify(cls, src_path: str) -> Optional[Tuple[ProductType, str]]:
        return identify_ps(src_path)
