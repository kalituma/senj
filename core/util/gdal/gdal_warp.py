from typing import Union
from osgeo import gdal
from osgeo.gdal import WarpOptions, Dataset

from core.util import epsg_to_wkt
from core.util.gdal import RESAMPLING_METHODS

def warp_gdal(ds:Dataset, snap_params: dict) -> Dataset:

    warp_option_dict = {}

    target_srs = snap_params['crs']
    src_srs = snap_params['src_crs']





    if 'pixelSizeX' in snap_params:
        warp_option_dict['xRes'] = snap_params['pixelSizeX']
        warp_option_dict['yRes'] = snap_params['pixelSizeY']

    # output_ds = gdal.Warp('', ds, options=warp_options)
    return output_ds

def _build_params(options:dict, build=False) -> WarpOptions:
    if build:
        return WarpOptions(**options)
    else:
        return options

def build_reprojection_params(from_srs:int, to_srs:int, build=False, **kwargs) -> Union[dict, WarpOptions]:
    from_srs_wkt = epsg_to_wkt(from_srs)
    to_srs_wkt = epsg_to_wkt(to_srs)

    warp_options = dict(
        **kwargs,
        srcSRS=from_srs_wkt,
        dstSRS=to_srs_wkt
    )

    return _build_params(warp_options, build)

def build_resample_params(res:float, resample_alg:str, build=False, **kwargs) -> Union[dict, WarpOptions]:

    resampleAlg = RESAMPLING_METHODS[resample_alg]

    warp_options = dict(
        **kwargs,
        xRes=res,
        yRes=res,
        resampleAlg=resampleAlg
    )
    return _build_params(warp_options, build)

def build_subset_params(bounds:list[float], bounds_srs:int, build=False, **kwargs) -> Union[dict, WarpOptions]:

    from_srs_wkt = epsg_to_wkt(bounds_srs)

    warp_options = dict(
        **kwargs,
        outputBounds=bounds,
        outputBoundsSRS=from_srs_wkt
    )

    return _build_params(warp_options, build)
