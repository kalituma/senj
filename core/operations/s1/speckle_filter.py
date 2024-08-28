from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import SPECKLE_FILTER_OP
from core.operations import ParamOp, SnappyOp

from core.util import assert_bnames, ProductType
from core.util.op import  call_constraint, op_constraint, OP_TYPE

from core.raster import Raster, RasterType
from core.util.snap import LEE_SIGMA, SIGMA_90, SIZE_3x3, SIZE_7x7, speckle_filter
if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SPECKLE_FILTER_OP, conf_no_arg_allowed=True)
@op_constraint(avail_op_types=[OP_TYPE.SNAP])
class SpeckleFilter(ParamOp, SnappyOp):
    def __init__(self, sourceBandNames:list[str]=None, filter:str=LEE_SIGMA, dampingFactor=2, filterSize:tuple=(3, 3), numberLooks:int=1,
                     windowSize:str=SIZE_7x7, targetWindowSizeStr:str=SIZE_3x3, sigma:str=SIGMA_90, anSize=50):
        super().__init__(SPECKLE_FILTER_OP)

        self.add_param(sourceBandNames=sourceBandNames, filter=filter, dampingFactor=dampingFactor, filterSizeX=filterSize[0], filterSizeY=filterSize[1],
                       numberLooksStr=str(numberLooks), windowSize=windowSize, targetWindowSizeStr=targetWindowSizeStr, sigmaStr=str(sigma), anSize=anSize)

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        if not self.get_param('sourceBandNames'):
            self.add_param(sourceBandNames=raster.get_band_names())
        else:
            assert_bnames(self.get_param('sourceBandNames'), raster.get_band_names(), msg=f'{self.get_param("sourceBandNames")} is not in {raster.get_band_names()}')

        raster.raw = speckle_filter(raster.raw, self.snap_params)
        raster = self.post_process(raster, context)
        return raster