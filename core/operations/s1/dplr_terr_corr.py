from typing import TYPE_CHECKING

from core import OPERATIONS
from core.operations import ParamOp, SnappyOp
from core.operations import TERR_CORR_OP
from core.util import assert_bnames, ProductType
from core.util.op import  call_constraint, MODULE_TYPE, op_constraint
from core.raster import Raster, RasterType
from core.util.snap import DemType, InterpolType, terrain_correction_func

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=TERR_CORR_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[MODULE_TYPE.SNAP])
class TerrainCorrection(ParamOp, SnappyOp):
    def __init__(self, bands:list[str]=None, dem_name:str='SRTM_3SEC',
                 pixel_spacing_meter:float=0.0, pixel_spacing_degree: float=0.0,
                 dem_method:str='BICUBIC_INTERPOLATION',
                 img_method:str='BICUBIC_INTERPOLATION',
                 save_dem: bool=False, map_projection:str= "WGS84(DD)"):

        super().__init__(TERR_CORR_OP)

        assert dem_name in [dem.name for dem in DemType], f"demName must be one of {DemType}"
        assert dem_method in [inter.name for inter in InterpolType], f"demResamplingMethod must be one of {InterpolType}"
        assert img_method in [inter.name for inter in InterpolType], f"imgResamplingMethod must be one of {InterpolType}"
        assert map_projection == "WGS84(DD)" or 'epsg' in map_projection.lower(), "mapProjection must be in WGS84(DD) or EPSG format"

        self.add_param(sourceBandNames=bands, demName=str(DemType[dem_name]), saveDem=save_dem,
                       pixelSpacingInMeter=pixel_spacing_meter, pixelSpacingInDegree=pixel_spacing_degree,
                       demResamplingMethod=str(InterpolType[dem_method]), imgResamplingMethod=str(InterpolType[img_method]),
                       mapProjection=map_projection)
    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if not self.get_param('sourceBandNames'):
            self.add_param(sourceBandNames=raster.get_band_names())
        else:
            assert_bnames(self.get_param('sourceBandNames'), raster.get_band_names(), msg=f'{self.get_param("sourceBandNames")} is not in {raster.get_band_names()}')

        raster.raw = terrain_correction_func(raster.raw, self.snap_params)
        raster = self.post_process(raster, context=context)
        return raster