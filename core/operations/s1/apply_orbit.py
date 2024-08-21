from typing import TYPE_CHECKING

from core import OPERATIONS
from core.util import op_product_type, check_module_type, ProductType
from core.operations import Op, APPLYORBIT_OP
from core.raster import Raster, RasterType


from core.util.snap import apply_orbit_func, make_meta_dict, ORBIT_TYPE

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=APPLYORBIT_OP)
class ApplyOrbit(Op):
    def __init__(self, orbitType:ORBIT_TYPE=ORBIT_TYPE.SENTINEL_PRECISE, polyDegree:int=3, continueOnFail:bool=False):
        super().__init__(APPLYORBIT_OP)
        self.ap_params = {
            'orbitType': str(orbitType),
            'polyDegree': polyDegree,
            'continueOnFail': continueOnFail
        }

    @check_module_type(RasterType.SNAP)
    @op_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        raster.raw = apply_orbit_func(raster.raw, params=self.ap_params)
        raster.meta_dict = make_meta_dict(raster.raw)
        raster = self.post_process(raster, context)
        return raster