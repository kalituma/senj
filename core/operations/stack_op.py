from typing import TYPE_CHECKING

from core.raster import merge_raster_func
from core.operations import Op
from core.operations import OPERATIONS, STACK_OP


if TYPE_CHECKING:
    from core.raster import Raster
@OPERATIONS.reg(name=STACK_OP)
class Stack(Op):
    def __init__(self, axis:int=0, bands:list=None):
        super().__init__(STACK_OP)
        self.axis = axis
        self.bands = bands

    def __call__(self, rasters:list["Raster"], *args, **kwargs):

        assert len(rasters) > 1, 'At least two rasters are required for stacking'

        merged_raster = merge_raster_func(rasters, self.bands)
        merged_raster = self.post_process(merged_raster, *args, **kwargs)
        return merged_raster