from typing import TYPE_CHECKING

from core import OPERATIONS
from core.operations import CachedOp, Context
from core.operations import ATMOSCORR_OP
from core.util.op import op_constraint, OP_TYPE

from core.raster.funcs import apply_atmos, write_l2r_as_map

if TYPE_CHECKING:
    from core.raster import Raster

@OPERATIONS.reg(name=ATMOSCORR_OP, conf_no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.SNAP, OP_TYPE.GDAL])
class AtmosCorr(CachedOp):
    def __init__(self):
        super().__init__(ATMOSCORR_OP)

    def __call__(self, raster:"Raster", context:Context, *args, **kwargs):

        x = x + 1
        att = self.post_process(**prev_att)
        return x, att