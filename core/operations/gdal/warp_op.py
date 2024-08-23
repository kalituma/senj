from typing import TYPE_CHECKING
from core import OPERATIONS

from core.operations import Op
from core.operations import WARP_OP
from core.util.op import available_op, OP_TYPE

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=WARP_OP, conf_no_arg_allowed=False)
@available_op(OP_TYPE.GDAL)
class Warp(Op):
    def __init__(self, x_res:float=None, y_res:float=None, resampling_type:str='nearest', projection:str=None, no_data:float=None):
        super().__init__(WARP_OP)
        self._resampling_type = resampling_type
        self._x_res = x_res
        self._y_res = y_res
        self._projection = projection

    def __call__(self, raster:"Raster", context:"Context", *args, **kwargs) -> "Raster":
        assert self._resolution is not None, 'Resolution must be set'
        assert len(self._resolution) == 2, 'Resolution must be set as (x_res, y_res)'

        # resample_op = Resample(self._module, out_ext=self._out_ext, resampling_type=self._resampling_type, resolution=self._resolution)
        # result = resample_op(raster)

        result.op_history.append(self.name)
        return result
