from typing import TYPE_CHECKING

from core import OPERATIONS
from core.util import ProductType
from core.util.op import allow_product_type, allow_module_type, available_op, OP_TYPE
from core.operations import Op, APPLYORBIT_OP
from core.raster import Raster, RasterType
from core.raster.funcs import create_band_name_idx

from core.util.snap import apply_orbit_func, make_meta_dict_from_product, ORBIT_TYPE

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=APPLYORBIT_OP, conf_no_arg_allowed=True)
@available_op(OP_TYPE.SNAP)
class ApplyOrbit(Op):

    def __init__(self, orbitType:ORBIT_TYPE=ORBIT_TYPE.SENTINEL_PRECISE, polyDegree:int=3, continueOnFail:bool=False):
        super().__init__(APPLYORBIT_OP)
        self.ap_params = {
            'orbitType': str(orbitType),
            'polyDegree': polyDegree,
            'continueOnFail': continueOnFail
        }

    @allow_module_type(RasterType.SNAP)
    @allow_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        raster.raw = apply_orbit_func(raster.raw, params=self.ap_params)
        meta_dict = make_meta_dict_from_product(raster.raw, raster.product_type)
        meta_dict = create_band_name_idx(meta_dict, raster.raw, product_type=raster.product_type, module_type=raster.module_type)
        raster.meta_dict = meta_dict
        raster = self.post_process(raster, context)
        return raster