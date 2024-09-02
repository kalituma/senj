from typing import TYPE_CHECKING
from core import OPERATIONS
from core.util.op import op_constraint, OP_TYPE
from core.operations import CONVERT_OP
from core.operations.parent import Op

from core.raster import RasterType
from core.raster.funcs import convert_raster

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=CONVERT_OP, conf_no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.CONVERT])
class Convert(Op):
    def __init__(self, to_module:str):
        super().__init__(CONVERT_OP)
        self._module:RasterType = RasterType.from_str(to_module.lower())
        self.op_type = OP_TYPE.from_str(to_module)

    def __call__(self, raster_obj:"Raster", context:"Context", *args, **kwargs) -> "Raster":

        if self._module == raster_obj.module_type:
            return raster_obj

        # result = update_cached_to_raw(raster_obj)
        result = convert_raster(raster_obj, out_module=self._module)
        result = self.post_process(result, context)

        return result

