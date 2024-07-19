from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import Op, CONVERT_OP

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=CONVERT_OP)
class Convert(Op):
    def __init__(self, module:str):
        super().__init__(CONVERT_OP)
        self._module = module

    def __call__(self, raster_obj:"Raster", context:"Context", *args):
        # prev_result = args[0]
        # assert isinstance(prev_result[0], np.ndarray), 'ConvertOp requires a numpy array'

        print()