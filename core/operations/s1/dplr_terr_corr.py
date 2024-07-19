NEAREST_NEIGHBOUR_NAME = "NEAREST_NEIGHBOUR"
BILINEAR_INTERPOLATION_NAME = "BILINEAR_INTERPOLATION"
CUBIC_CONVOLUTION_NAME = "CUBIC_CONVOLUTION"
BISINC_5_POINT_INTERPOLATION_NAME = "BISINC_5_POINT_INTERPOLATION"
BISINC_11_POINT_INTERPOLATION_NAME = "BISINC_11_POINT_INTERPOLATION"
BISINC_21_POINT_INTERPOLATION_NAME = "BISINC_21_POINT_INTERPOLATION"
BICUBIC_INTERPOLATION_NAME = "BICUBIC_INTERPOLATION"

COPERNICUS_30 = "Copernicus 30m Global DEM"
STRM_3SEC = "SRTM 3Sec"
STRM_1SEC_HGT = "SRTM 1Sec HGT"
SRTM_1SEC_GRD = "SRTM 1Sec Grid"
ASTER_1SEC = "ASTER 1Sec GDEM"
ACE30 = "ACE30"
ACE2_5 = "ACE2_5Min"
GETASSE30 = "GETASSE30"

from core import OPERATIONS
from core.operations import Op, TERR_CORR_OP
from core.util import check_product_type
from core.raster import Raster, ProductType
from core.raster.gpf_module import terrain_correction_func

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
    def __call__(self, raster:Raster, *args, **kwargs):

        if not self.terr_corr_params['sourceBandNames']:
            self.terr_corr_params['sourceBandNames'] = raster.get_band_names()

        raster.raw = terrain_correction_func(raster.raw, self.terr_corr_params)
        raster = self.post_process(raster)
        return raster