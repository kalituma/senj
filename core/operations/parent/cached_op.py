from typing import TYPE_CHECKING
from core.operations.parent import Op

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

class CachedOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def __call__(self, *args, **kwargs):
        pass

    def pre_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        pass

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        #Todo: update cached raster to raw after checking the context
        raster = super().post_process(raster, context)
        return raster