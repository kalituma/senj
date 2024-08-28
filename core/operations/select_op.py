from typing import TYPE_CHECKING, List, AnyStr, Union
from core.operations.parent import SelectOp
from core.operations import OPERATIONS, SELECT_OP
from core.util.op import OP_TYPE, op_constraint

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=SELECT_OP, no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.GDAL, OP_TYPE.SNAP])
class Select(SelectOp):
    def __init__(self, bands:List[Union[int, AnyStr]]):
        super().__init__(SELECT_OP)
        self._selected_bands = bands

    def __call__(self, raster:"Raster", context:"Context", *args):
        raster = self.pre_process(raster, selected_bands_or_indices=self._selected_bands, band_select=True)
        raster = self.post_process(raster, context)
        return raster