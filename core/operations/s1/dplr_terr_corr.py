from typing import TYPE_CHECKING

from core import OPERATIONS
from core.operations import Op, TERR_CORR_OP
from core.util import check_product_type
from core.raster import Raster, ProductType
from core.raster.gpf_module import terrain_correction_func, STRM_3SEC, BILINEAR_INTERPOLATION_NAME

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=TERR_CORR_OP)
class TerrainCorrection(Op):
    def __init__(self, sourceBandNames:list[str]=None, demName:str=STRM_3SEC,
                 pixelSpacingInMeter:float=0.0, pixelSpacingInDegree: float=0.0,
                 demResamplingMethod:str=BILINEAR_INTERPOLATION_NAME, imgResamplingMethod:str=BILINEAR_INTERPOLATION_NAME,
                 saveDem: bool=False, mapProjection:str="WGS84(DD)"):

        super().__init__(TERR_CORR_OP)

        self.terr_corr_params = {
            'sourceBandNames' : sourceBandNames,
            'demName': demName,
            'saveDem': saveDem,
            'pixelSpacingInMeter': pixelSpacingInMeter,
            'pixelSpacingInDegree': pixelSpacingInDegree,
            'demResamplingMethod': demResamplingMethod,
            'imgResamplingMethod': imgResamplingMethod,
            'mapProjection': mapProjection
        }

    @check_product_type(ProductType.S1)
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if not self.terr_corr_params['sourceBandNames']:
            self.terr_corr_params['sourceBandNames'] = raster.get_band_names()

        raster.raw = terrain_correction_func(raster.raw, self.terr_corr_params)
        raster = self.post_process(raster, context=context)
        return raster