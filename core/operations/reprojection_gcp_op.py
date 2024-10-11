from core.operations.parent import ParamOp, WarpOp
from core.operations import OPERATIONS, GCP_REPROJECT_OP
from core.logic import Context
from core.raster import Raster, ModuleType
from core.raster.funcs import get_epsg, get_res

from core.util.snap import reproject_gpf, find_gt_from_product
from core.util.op import OP_Module_Type, op_constraint
from core.util.gdal import is_epsg_code_valid, unit_from_epsg

GDAL_RESAMPLING_METHODS = ['nearest', 'bilinear', 'bicubic', 'cubicspline', 'lanczos']

@OPERATIONS.reg(name=GCP_REPROJECT_OP, no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class GCPReproject(WarpOp):
    def __init__(self, epsg:int=None, resam=None):
        pass