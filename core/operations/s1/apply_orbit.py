from typing import TYPE_CHECKING

from core import OPERATIONS
from core.util import ProductType
from core.util.op import call_constraint, op_constraint, OP_Module_Type
from core.operations import APPLYORBIT_OP
from core.operations.parent import ParamOp, SnappyOp
from core.raster import Raster, ModuleType
from core.raster.funcs import init_bname_index_in_meta

from core.util.snap import apply_orbit_func, make_meta_dict_from_product, ORBIT_TYPE

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=APPLYORBIT_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP])
class ApplyOrbit(ParamOp, SnappyOp):
    def __init__(self, orbit_type:str='SENTINEL_PRECISE', poly_degree:int=3, continue_on_fail:bool=False):
        super().__init__(APPLYORBIT_OP)
        self.add_param(orbitType=str(ORBIT_TYPE[orbit_type]), polyDegree=poly_degree, continueOnFail=continue_on_fail)

    @call_constraint(module_types=[ModuleType.SNAP], product_types=[ProductType.S1], ext=['safe'])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        raster.raw = apply_orbit_func(raster.raw, params=self.snap_params)

        # update meta_dict with new orbit vectors
        meta_dict = make_meta_dict_from_product(raster.raw, raster.product_type)
        meta_dict = init_bname_index_in_meta(meta_dict, raster.raw, product_type=raster.product_type, module_type=raster.module_type)
        raster.meta_dict = meta_dict

        raster = self.post_process(raster, context)

        return raster