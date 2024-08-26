from osgeo import osr, ogr
from core.operations import SnapOp
from core.operations import OPERATIONS, REPROJECT_OP
from core.logic import Context
from core.raster import Raster, RasterType, get_epsg
from core.util.snap import reproject_gpf
from core.util.op import OP_TYPE, available_op
from core.util.gdal import check_epsg_code_valid, warp_gdal

resampling_methods = ['nearest', 'bilinear', 'bicubic', 'cubicspline', 'lanczos']

@OPERATIONS.reg(name=REPROJECT_OP, no_arg_allowed=False)
@available_op(OP_TYPE.GDAL, OP_TYPE.SNAP)
class Reproject(SnapOp):
    def __init__(self, epsg:int=4326, pixel_size:float=None, resampling_method:str='nearest'):
        super().__init__(REPROJECT_OP)

        resampling_method = resampling_method.lower()
        assert resampling_method.lower() in resampling_methods, f'resampling_method should be one of {resampling_methods}'
        check_epsg_code_valid(epsg)

        self.add_param(crs=f'EPSG:{epsg}', resamplingName=resampling_method.title())

        if pixel_size:
            self.add_param(pixelSizeX=pixel_size, pixelSizeY=pixel_size)

        self.epsg:int = epsg
        self.resampling_method:str = resampling_method

    def __call__(self, raster:"Raster", context:"Context", *args):

        if raster.module_type == RasterType.SNAP:
            dataset = reproject_gpf(raster.raw, self.snap_params)
        elif raster.module_type == RasterType.GDAL:
            # prev_snap_params = context.get('warp_params')
            src_epsg = get_epsg(raster)
            self.add_param(src_crs=f'EPSG:{src_epsg}')
            dataset = warp_gdal(raster.raw, self.snap_params)

        raster.raw = dataset
        result = self.post_process(raster, context)

        return result