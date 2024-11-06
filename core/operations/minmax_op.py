from typing import TYPE_CHECKING

from core.operations import OPERATIONS, MINMAX_CLIP_OP

from core.operations.parent import CachedOp
from core.util.op import OP_Module_Type, op_constraint
from core.raster.funcs import clip_value

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=MINMAX_CLIP_OP, no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL])
class MinMax_Clip(CachedOp):
    def __init__(self, min_val:float, max_val:float, min_clip_val:float, max_clip_val:float):
        super().__init__(MINMAX_CLIP_OP)
        self._min_val = min_val
        self._max_val = max_val
        self._min_clip_val = min_clip_val
        self._max_clip_val = max_clip_val


    def __call__(self, raster:"Raster", context:"Context", *args):

        raster = self.pre_process(raster, context, bands_to_load=raster.get_band_names())
        raster = clip_value(raster, self._min_val, self._max_val, self._min_clip_val, self._max_clip_val)
        self.post_process(raster, context, clear=True)
        return raster