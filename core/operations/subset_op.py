from warnings import warn
from typing import TYPE_CHECKING, List, Union, AnyStr
from core.operations import OPERATIONS, SUBSET_OP, ParamOp
from core.raster import Raster, RasterType, get_epsg
from core.util import region_to_wkt, assert_bnames
from core.util.op import OP_TYPE, op_constraint
from core.util.snap import subset_gpf
from core.util.gdal import make_transform

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SUBSET_OP, no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.GDAL, OP_TYPE.SNAP])
class Subset(ParamOp):
    def __init__(self, bounds:list[float], copy_meta:bool=True):
        super().__init__(SUBSET_OP)

        self.add_param(copyMetadata=copy_meta)
        assert len(bounds) == 4, 'bounds should have 4(min_x, max_y, max_x, min_y) elements'

        # self._selected_bands = bands
        self._bounds = bounds
        self._bounds_wkt = region_to_wkt(bounds)
        self.add_param(geoRegion=self._bounds_wkt)

    # def check_epsg(self, raster:Raster):
    #     raster_epsg = get_epsg(raster)
    #     if raster_epsg != self._bounds_epsg:
    #         transform = make_transform(self._bounds_epsg, raster_epsg)
    #         ul_x, ul_y, _ = transform.TransformPoint(self._bounds[1], self._bounds[0])
    #         lr_x, lr_y, _ = transform.TransformPoint(self._bounds[3], self._bounds[2])
    #         bounds = [ul_x, ul_y, lr_x, lr_y]
    #         wkt = region_to_wkt(bounds)
    #         self.subset_params['geoRegion'] = wkt

    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if raster.module_type == RasterType.SNAP:
            self.add_param(bandNames=raster.get_band_names())
            tiePoints = raster.get_tie_point_grid_names()
            if tiePoints:
                self.add_param(tiePointGridNames=tiePoints)
            raster.raw = subset_gpf(raster.raw, self.snap_params)

        elif raster.module_type == RasterType.GDAL:
        #     if context.get('gdal'):
            # if self._selected_bands:
            #     assert_bnames(self._selected_bands, raster.get_band_names(), f'selected bands{self._selected_bands} should be in source bands({raster.get_band_names()})')
            #     if len(self._selected_bands) < len(raster.get_band_names()):
            #         result = select_band_raster(raster, self._selected_bands)
            pass
        else:
            raise NotImplementedError(f"Subset operation not implemented for {raster.module_type}")

        raster = self.post_process(raster, context)

        return raster