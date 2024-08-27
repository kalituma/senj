from typing import TYPE_CHECKING

from core import OPERATIONS
from core.util import ProductType
from core.util.op import call_constraint, op_constraint, OP_TYPE
from core.operations import ParamOp, APPLYORBIT_OP
from core.raster import Raster, RasterType
from core.raster.funcs import create_band_name_idx

from core.util.snap import apply_orbit_func, make_meta_dict_from_product, ORBIT_TYPE

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=APPLYORBIT_OP, conf_no_arg_allowed=True)
@op_constraint(avail_op_types=[OP_TYPE.SNAP])
class ApplyOrbit(ParamOp):

    def __init__(self, orbitType:ORBIT_TYPE=ORBIT_TYPE.SENTINEL_PRECISE, polyDegree:int=3, continueOnFail:bool=False):
        super().__init__(APPLYORBIT_OP)
        self.add_param(orbitType=str(orbitType), polyDegree=polyDegree, continueOnFail=continueOnFail)

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        raster.raw = apply_orbit_func(raster.raw, params=self.snap_params)
        meta_dict = make_meta_dict_from_product(raster.raw, raster.product_type)
        meta_dict = create_band_name_idx(meta_dict, raster.raw, product_type=raster.product_type, module_type=raster.module_type)
        raster.meta_dict = meta_dict
        raster = self.post_process(raster, context)
        return raster