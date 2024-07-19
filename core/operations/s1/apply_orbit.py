from typing import TYPE_CHECKING

from core import OPERATIONS
from core.util import check_product_type
from core.operations import Op, APPLYORBIT_OP
from core.raster import Raster, ProductType

from core.raster.gpf_module import apply_orbit_func, ORBIT_TYPE

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=APPLYORBIT_OP)
class ApplyOrbit(Op):
    def __init__(self, orbitType:str=ORBIT_TYPE['SENTINEL_PRECISE'], polyDegree:int=3, continueOnFail:bool=False):
        super().__init__(APPLYORBIT_OP)
        self.ap_params = {
            'orbitType': orbitType,
            'polyDegree': polyDegree,
            'continueOnFail': continueOnFail
        }

    @check_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        assert raster.product_type == ProductType.S1, f'Product type should be Sentinel-1, but got {raster.product_type.value}'
        raster.raw = apply_orbit_func(raster.raw, params=self.ap_params)
        raster = self.post_process(raster, context)
        return raster