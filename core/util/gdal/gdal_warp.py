from typing import Union
from osgeo import gdal
from osgeo.gdal import WarpOptions, Dataset

from core.util import epsg_to_wkt
from core.util.gdal import RESAMPLING_METHODS, copy_ds

SNAP_TO_GDAL_RESAMPLING = {
    'nearest': 'near',
    'bicubic': 'cubic'
}

def snap_params_to_gdal_warp_options(snap_params: dict) -> dict:

    warp_option_dict = {}

    if 'src_crs' in snap_params:
        warp_option_dict['srcSRS'] = snap_params['src_crs']
        warp_option_dict['dstSRS'] = snap_params['crs']
    if 'resamplingName' in snap_params:
        if snap_params['resamplingName'] in SNAP_TO_GDAL_RESAMPLING:
            warp_option_dict['resampleAlg'] = SNAP_TO_GDAL_RESAMPLING[snap_params['resamplingName']]
        else:
            warp_option_dict['resampleAlg'] = snap_params['resamplingName']

    if 'pixelSizeX' in snap_params and 'pixelSizeY' in snap_params:
        warp_option_dict['xRes'] = snap_params['pixelSizeX']
        warp_option_dict['yRes'] = snap_params['pixelSizeY']

    if 'outputBounds' in snap_params:
        warp_option_dict['outputBounds'] = snap_params['outputBounds']
        warp_option_dict['outputBoundsSRS'] = 'EPSG:4326'

    return warp_option_dict

def warp_gdal(ds:Dataset, snap_params: dict) -> Dataset:

    warp_params = snap_params_to_gdal_warp_options(snap_params)
    warp_options = WarpOptions(**warp_params)
    output_ds = gdal.Warp('/vsimem/memory_warp', ds, options=warp_options)

    return output_ds

