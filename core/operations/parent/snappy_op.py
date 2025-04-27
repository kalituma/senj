from typing import TYPE_CHECKING
from core.operations.parent import Op
from core.raster.funcs.meta import MetaBandsManager

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

class SnappyOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        super().post_process(raster, context)
        MetaBandsManager(raster).update_band_mapping(raster.get_band_names('raw'))
        return raster