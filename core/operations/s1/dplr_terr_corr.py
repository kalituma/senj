from typing import TYPE_CHECKING, Union

from core import OPERATIONS
from core.operations import TERR_CORR_OP
from core.operations.parent import SelectOp, SnappyOp, ParamOp

from core.util import assert_bnames, ProductType
from core.util.op import  call_constraint, OP_Module_Type, op_constraint
from core.raster import Raster, ModuleType
from core.raster.funcs import get_band_name_and_index
from core.util.snap import DemType, InterpolType, terrain_correction_func
from core.util.gdal import is_epsg_code_valid


if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=TERR_CORR_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP])
class TerrainCorrection(ParamOp, SelectOp, SnappyOp):
    def __init__(self, bands:list[Union[str,int]]=None, dem_name:str='SRTM_3SEC',
                 pixel_spacing_meter:float=0.0, pixel_spacing_degree: float=0.0,
                 dem_method:str='BICUBIC_INTERPOLATION',
                 img_method:str='BICUBIC_INTERPOLATION',
                 save_dem: bool=False, epsg:int=4326):

        super().__init__(TERR_CORR_OP)

        assert dem_name in [dem.name for dem in DemType], f"demName must be one of {DemType}"
        assert dem_method in [inter.name for inter in InterpolType], f"demResamplingMethod must be one of {InterpolType}"
        assert img_method in [inter.name for inter in InterpolType], f"imgResamplingMethod must be one of {InterpolType}"

        is_epsg_code_valid(epsg)
        if epsg == 4326:
            map_projection = 'WGS84(DD)'
        else:
            map_projection = f'EPSG:{epsg}'

        self._selected_name_or_index = bands

        self.add_param(demName=str(DemType[dem_name]), saveDem=save_dem,
                       pixelSpacingInMeter=pixel_spacing_meter, pixelSpacingInDegree=pixel_spacing_degree,
                       demResamplingMethod=str(InterpolType[dem_method]), imgResamplingMethod=str(InterpolType[img_method]),
                       mapProjection=map_projection)
    @call_constraint(module_types=[ModuleType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if self._selected_name_or_index:
            selected_bands, _ = get_band_name_and_index(raster, self._selected_name_or_index)
        else:
            selected_bands = raster.get_band_names()

        self.add_param(sourceBandNames=selected_bands)

        raster.raw = terrain_correction_func(raster.raw, self.snap_params)
        raster = self.post_process(raster, context=context)
        return raster