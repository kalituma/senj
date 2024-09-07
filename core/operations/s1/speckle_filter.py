from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import SPECKLE_FILTER_OP
from core.operations import ParamOp, SnappyOp

from core.util import assert_bnames, ProductType
from core.util.op import  call_constraint, op_constraint, MODULE_TYPE

from core.raster import Raster, RasterType
from core.util.snap import LEE_SIGMA, SIGMA_90, SIZE_3x3, SIZE_7x7, speckle_filter
if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SPECKLE_FILTER_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[MODULE_TYPE.SNAP])
class SpeckleFilter(ParamOp, SnappyOp):
    def __init__(self, bands:list[str]=None, filter:str=LEE_SIGMA, damping_factor=2, filter_size:tuple=(3, 3), number_looks:int=1,
                 window_size:str=SIZE_7x7, target_window_size:str=SIZE_3x3, sigma:str=SIGMA_90, an_size=50):
        super().__init__(SPECKLE_FILTER_OP)

        self.add_param(sourceBandNames=bands, filter=filter, dampingFactor=damping_factor, filterSizeX=filter_size[0], filterSizeY=filter_size[1],
                       numberLooksStr=str(number_looks), windowSize=window_size, targetWindowSizeStr=target_window_size, sigmaStr=str(sigma), anSize=an_size)

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        if not self.get_param('sourceBandNames'):
            self.add_param(sourceBandNames=raster.get_band_names())
        else:
            assert_bnames(self.get_param('sourceBandNames'), raster.get_band_names(), msg=f'{self.get_param("sourceBandNames")} is not in {raster.get_band_names()}')

        raster.raw = speckle_filter(raster.raw, self.snap_params)
        raster = self.post_process(raster, context)
        return raster