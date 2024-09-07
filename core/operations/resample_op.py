import numpy as np
from copy import deepcopy
from core.operations.parent import ParamOp, WarpOp
from core.operations import OPERATIONS, RESAMPLE_OP
from core.logic import Context
from core.raster import Raster, RasterType, get_epsg, get_res
from core.util.snap import reproject_gpf, find_gt_from_product
from core.util.op import MODULE_TYPE, op_constraint
from core.util.gdal import is_epsg_code_valid

SNAP_RESAMPLING_METHODS = ['nearest', 'bilinear', 'bicubic']
GDAL_RESAMPLING_METHODS = ['nearest', 'bilinear', 'bicubic', 'cubicspline', 'lanczos']
ALL_RESAMPLING_METHODS = GDAL_RESAMPLING_METHODS

@OPERATIONS.reg(name=RESAMPLE_OP, no_arg_allowed=False)
@op_constraint(avail_module_types=[MODULE_TYPE.GDAL, MODULE_TYPE.SNAP])
class Resample(ParamOp, WarpOp):
    def __init__(self, epsg:int=None, pixel_size:float=None, resampling_method:str= 'nearest'):
        super().__init__(RESAMPLE_OP)

        assert resampling_method in ALL_RESAMPLING_METHODS, f'resampling_method should be one of {ALL_RESAMPLING_METHODS}'

        self.resampling_method:str = resampling_method.lower()
        self.add_param(resamplingName=resampling_method)

        if pixel_size:
            self.add_param(pixelSizeX=pixel_size, pixelSizeY=pixel_size)

        self.epsg:int = epsg

    def __call__(self, raster:"Raster", context:"Context", *args):

        if self.module_type == MODULE_TYPE.SNAP:
            assert self.resampling_method in SNAP_RESAMPLING_METHODS, f'resampling_method should be one of {SNAP_RESAMPLING_METHODS}'
        elif self.module_type == MODULE_TYPE.GDAL:
            assert self.resampling_method in GDAL_RESAMPLING_METHODS, f'resampling_method should be one of {GDAL_RESAMPLING_METHODS}'
        else:
            raise NotImplementedError(f"Resample method cannot be executed if op_type is {self.module_type}")

        if self.epsg is not None:
            is_epsg_code_valid(self.epsg)
            usr_epsg = f'EPSG:{self.epsg}'
        else:
            usr_epsg = f'EPSG:{get_epsg(raster)}'

        self.add_param(crs=usr_epsg)
        src_epsg = f'EPSG:{get_epsg(raster)}'

        res = get_res(raster)
        usr_res = self.get_param('pixelSizeX')

        if not usr_res:
            usr_res = res

        if src_epsg != usr_epsg or not np.isclose(res, usr_res):

            if self.module_type == MODULE_TYPE.SNAP:
                assert raster.module_type == RasterType.SNAP, 'Resample operation is only available for SNAP module'
                dataset = reproject_gpf(raster.raw, self.snap_params)
            elif self.module_type == MODULE_TYPE.GDAL:
                assert raster.module_type == RasterType.GDAL, 'Resample operation is only available for GDAL module'
                self.add_param(src_crs=src_epsg)
                cur_params = deepcopy(self.snap_params)
                dataset, context = self.call_warp(raster.raw, cur_params, context)
            else:
                raise NotImplementedError(f"Resample method for {raster.module_type.__str__()} is not implemented yet")

            raster.raw = dataset

        raster = self.post_process(raster, context)

        return raster