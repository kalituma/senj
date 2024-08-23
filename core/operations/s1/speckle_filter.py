from typing import TYPE_CHECKING
from core import OPERATIONS
from core.operations import Op, SPECKLE_FILTER_OP

from core.util import ProductType
from core.util.op import allow_product_type, allow_module_type, available_op, OP_TYPE

from core.raster import Raster, RasterType
from core.util.snap import LEE_SIGMA, SIGMA_90, SIZE_3x3, SIZE_7x7, speckle_filter
if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SPECKLE_FILTER_OP, conf_no_arg_allowed=True)
@available_op(OP_TYPE.SNAP)
class SpeckleFilter(Op):
    def __init__(self, sourceBandNames:list[str]=None, filter:str=LEE_SIGMA, dampingFactor=2, filterSize:tuple=(3, 3), numberLooks:int=1,
                     windowSize:str=SIZE_7x7, targetWindowSizeStr:str=SIZE_3x3, sigma:str=SIGMA_90, anSize=50):
        super().__init__(SPECKLE_FILTER_OP)

        self.speckle_filter_params = {
            'sourceBandNames': sourceBandNames,
            'filter': filter,
            'dampingFactor': dampingFactor,
            'filterSizeX': filterSize[0],
            'filterSizeY': filterSize[1],
            'numberLooksStr': str(numberLooks),
            'windowSize': windowSize,
            'targetWindowSizeStr': targetWindowSizeStr,
            'sigmaStr': str(sigma),
            'anSize': anSize
        }

    @allow_module_type(RasterType.SNAP)
    @allow_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        if not self.speckle_filter_params['sourceBandNames']:
            self.speckle_filter_params['sourceBandNames'] = raster.get_band_names()

        raster.raw = speckle_filter(raster.raw, self.speckle_filter_params)
        raster = self.post_process(raster)
        return raster