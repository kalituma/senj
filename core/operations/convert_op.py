from typing import TYPE_CHECKING
from core import OPERATIONS
from core.util.op import op_constraint, OP_Module_Type
from core.operations import CONVERT_OP
from core.operations.parent import Op

from core.raster import ModuleType
from core.raster.funcs.converter import FormatConverter

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=CONVERT_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.CONVERT])
class Convert(Op):
    def __init__(self, to_module:str):
        super().__init__(CONVERT_OP)
        self._module:ModuleType = ModuleType.from_str(to_module.lower())

    def __call__(self, raster_obj:"Raster", context:"Context", *args, **kwargs) -> "Raster":

        if self._module == raster_obj.module_type:
            return raster_obj

        result = FormatConverter.convert(raster_obj, self._module)
        result = self.post_process(result, context)

        return result

