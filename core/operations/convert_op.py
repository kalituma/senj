from typing import TYPE_CHECKING
from core import OPERATIONS
from core.raster import RasterType
from core.util.op import available_op, OP_TYPE
from core.operations import Op, CONVERT_OP

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=CONVERT_OP, conf_no_arg_allowed=False)
@available_op(OP_TYPE.CONVERT)
class Convert(Op):
    def __init__(self, to_module:str):
        super().__init__(CONVERT_OP)
        self._to_module = RasterType.from_str(to_module.lower())

    def __call__(self, raster_obj:"Raster", context:"Context", *args):
        # prev_result = args[0]
        # assert isinstance(prev_result[0], np.ndarray), 'ConvertOp requires a numpy array'

        print()