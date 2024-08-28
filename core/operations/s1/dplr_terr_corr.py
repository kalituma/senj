from typing import TYPE_CHECKING

from core import OPERATIONS
from core.operations import ParamOp, SnappyOp
from core.operations import TERR_CORR_OP
from core.util import assert_bnames, ProductType
from core.util.op import  call_constraint, OP_TYPE, op_constraint
from core.raster import Raster, RasterType
from core.util.snap import DemType, InterpolType, terrain_correction_func

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=TERR_CORR_OP, conf_no_arg_allowed=True)
@op_constraint(avail_op_types=[OP_TYPE.SNAP])
class TerrainCorrection(ParamOp, SnappyOp):
    def __init__(self, sourceBandNames:list[str]=None, demName:DemType=DemType.SRTM_3SEC,
                 pixelSpacingInMeter:float=0.0, pixelSpacingInDegree: float=0.0,
                 demResamplingMethod:InterpolType=InterpolType.BICUBIC_INTERPOLATION,
                 imgResamplingMethod:InterpolType=InterpolType.BICUBIC_INTERPOLATION,
                 saveDem: bool=False, mapProjection:str="WGS84(DD)"):

        super().__init__(TERR_CORR_OP)

        assert str(demName) in [dem.value for dem in DemType], f"demName must be one of {DemType}"
        assert str(demResamplingMethod) in [inter.value for inter in InterpolType], f"demResamplingMethod must be one of {InterpolType}"
        assert str(imgResamplingMethod) in [inter.value for inter in InterpolType], f"imgResamplingMethod must be one of {InterpolType}"
        assert mapProjection == "WGS84(DD)" or 'epsg' in mapProjection.lower(), "mapProjection must be in WGS84(DD) or EPSG format"

        self.add_param(sourceBandNames=sourceBandNames, demName=str(demName), saveDem=saveDem,
                       pixelSpacingInMeter=pixelSpacingInMeter, pixelSpacingInDegree=pixelSpacingInDegree,
                       demResamplingMethod=str(demResamplingMethod), imgResamplingMethod=str(imgResamplingMethod),
                       mapProjection=mapProjection)
    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if not self.get_param('sourceBandNames'):
            self.add_param(sourceBandNames=raster.get_band_names())
        else:
            assert_bnames(self.get_param('sourceBandNames'), raster.get_band_names(), msg=f'{self.get_param("sourceBandNames")} is not in {raster.get_band_names()}')

        raster.raw = terrain_correction_func(raster.raw, self.snap_params)
        raster = self.post_process(raster, context=context)
        return raster