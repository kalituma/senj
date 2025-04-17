from typing import TYPE_CHECKING, List, Union, AnyStr
from copy import deepcopy

from core.operations.parent import ParamOp, WarpOp
from core.operations import OPERATIONS, SUBSET_OP
from core.raster import Raster, ModuleType
from core.util import region_to_wkt, assert_bnames, make_transform
from core.util.op import OP_Module_Type, op_constraint
from core.util.snap import subset_gpf
from core.util.gdal import is_epsg_code_valid
from core.util.snap import find_epsg_from_product

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SUBSET_OP, no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Subset(ParamOp, WarpOp):
    def __init__(self, bounds:list[float], bounds_epsg:int=4326,  copy_meta:bool=True):
        super().__init__(SUBSET_OP)

        self.add_param(copyMetadata=copy_meta)
        assert len(bounds) == 4, 'bounds should have 4(min_x, max_y, max_x, min_y) elements'

        # self._selected_bands = bands
        self._bounds = bounds
        self._bounds_epsg = bounds_epsg

        is_epsg_code_valid(bounds_epsg)
        if bounds_epsg == 4326:
            self._bounds_wkt = region_to_wkt(bounds)
        else:
            transform = make_transform(bounds_epsg, 4326)
            ul_y, ul_x, _ = transform.TransformPoint(self._bounds[0], self._bounds[1])
            lr_y, lr_x, _ = transform.TransformPoint(self._bounds[2], self._bounds[3])
            self._bounds = [ul_x, ul_y, lr_x, lr_y]
            self._bounds_wkt = region_to_wkt(self._bounds)
        self.add_param(geoRegion=self._bounds_wkt)

    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if raster.module_type == ModuleType.SNAP:
            assert self.module_type == OP_Module_Type.SNAP, 'Subset operation is only available for SNAP module'            

            self.add_param(bandNames=raster.get_band_names())
            tiePoints = raster.get_tie_point_grid_names()
            if tiePoints:
                self.add_param(tiePointGridNames=tiePoints)
            raster.raw = subset_gpf(raster.raw, self.snap_params)
        elif raster.module_type == ModuleType.GDAL:
            assert self.module_type == OP_Module_Type.GDAL, 'Subset operation is only available for GDAL module'
            cur_params = deepcopy(self.snap_params)
            cur_params['outputBounds'] = [self._bounds[0], self._bounds[3], self._bounds[2], self._bounds[1]]
            raster.raw, context = self.call_warp(raster.raw, cur_params, context)
        else:
            raise NotImplementedError(f"Subset operation not implemented for {raster.module_type}")

        raster = self.post_process(raster, context)

        return raster