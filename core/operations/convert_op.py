from typing import TYPE_CHECKING
from core import OPERATIONS
from core.util.op import available_op, OP_TYPE
from core.operations import Op, CONVERT_OP

from core.raster import RasterType
from core.raster.funcs import convert_raster, update_cached_to_raw

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=CONVERT_OP, conf_no_arg_allowed=False)
@available_op(OP_TYPE.CONVERT)
class Convert(Op):
    def __init__(self, to_module:str):
        super().__init__(CONVERT_OP)
        self._to_module:RasterType = RasterType.from_str(to_module.lower())

    def __call__(self, raster_obj:"Raster", context:"Context", *args, **kwargs) -> "Raster":

        if self._to_module == raster_obj.module_type:
            return raster_obj

        result = update_cached_to_raw(raster_obj)
        result = convert_raster(result, out_module=self._to_module)
        result = self.post_process(result, context)

        return result

