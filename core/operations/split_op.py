from typing import TYPE_CHECKING

from core.util.op import OP_Module_Type, op_constraint
from core.operations.parent import Op
from core.operations import OPERATIONS, SPLIT_OP
from core.raster.funcs import split_raster

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=SPLIT_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Split(Op):
    def __init__(self, bands:list=None):
        super().__init__(SPLIT_OP)
        self.bands = bands

    def __call__(self, raster:"Raster", context:"Context", *args) -> list["Raster"]:

        results = split_raster(raster, self.bands)

        for res in results:
            res.op_history.append(self.name)

        return results