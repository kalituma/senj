import numpy as np
from osgeo import osr, ogr
from core.operations.parent import ParamOp
from core.operations import OPERATIONS, RESAMPLE_OP
from core.logic import Context
from core.raster import Raster, RasterType, get_epsg, get_res
from core.util.snap import reproject_gpf, find_gt_from_product
from core.util.op import OP_TYPE, op_constraint
from core.util.gdal import is_epsg_code_valid, warp_gdal

SNAP_RESAMPLING_METHODS = ['nearest', 'bilinear', 'bicubic']
GDAL_RESAMPLING_METHODS = ['nearest', 'bilinear', 'bicubic', 'cubicspline', 'lanczos']

@OPERATIONS.reg(name=RESAMPLE_OP, no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.GDAL, OP_TYPE.SNAP])
class Resample(ParamOp):
    def __init__(self, epsg:int=4326, pixel_size:float=None, resampling_method:str='nearest'):
        super().__init__(RESAMPLE_OP)

        resampling_method = resampling_method.lower()

        if self.op_type == OP_TYPE.SNAP:
            assert resampling_method in SNAP_RESAMPLING_METHODS, f'resampling_method should be one of {SNAP_RESAMPLING_METHODS}'
        elif self.op_type == OP_TYPE.GDAL:
            assert resampling_method in GDAL_RESAMPLING_METHODS, f'resampling_method should be one of {GDAL_RESAMPLING_METHODS}'
        else:
            raise NotImplementedError(f"Resample method for {self.op_type.__str__()} is not implemented yet")

        is_epsg_code_valid(epsg)
        self.add_param(crs=f'EPSG:{epsg}', resamplingName=resampling_method)

        if pixel_size:
            self.add_param(pixelSizeX=pixel_size, pixelSizeY=pixel_size)

        self.epsg:int = epsg
        self.resampling_method:str = resampling_method

    def __call__(self, raster:"Raster", context:"Context", *args):

        src_epsg = f'EPSG:{get_epsg(raster)}'
        usr_epsg = self.get_param('crs')

        res = get_res(raster)
        usr_res = self.get_param('pixelSizeX')

        if not usr_res:
            usr_res = res

        if src_epsg != usr_epsg or not np.isclose(res, usr_res):

            if raster.module_type == RasterType.SNAP:
                dataset = reproject_gpf(raster.raw, self.snap_params)
            elif raster.module_type == RasterType.GDAL:
                # prev_snap_params = context.get('warp_params')
                self.add_param(src_crs=src_epsg)
                dataset = warp_gdal(raster.raw, self.snap_params)
            else:
                raise NotImplementedError(f"Resample method for {raster.module_type.__str__()} is not implemented yet")

            raster.raw = dataset

        result = self.post_process(raster, context)

        return result