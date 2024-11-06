from typing import Union, AnyStr, List
from core.operations.parent import WarpOp, SelectOp
from core.operations import OPERATIONS, GCP_REPROJECT_OP
from core.logic import Context
from core.raster import Raster, ModuleType

from core.util import str_to_hash
from core.util.op import OP_Module_Type, op_constraint
from core.util.gdal import is_epsg_code_valid, unit_from_epsg, read_gdal_bands, create_gcp, reproject_arr_using_gcp

GDAL_RESAMPLING_METHODS = ['nearest', 'bilinear', 'cubic', 'cubicspline', 'lanczos']

@OPERATIONS.reg(name=GCP_REPROJECT_OP, no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL])
class GCPReproject(SelectOp):
    def __init__(self, lat_band:str, lng_band:str, pixel_size:float, bands:List[Union[int,AnyStr]]=None,
                 gcp_epsg:int=4326, no_data:Union[int,float]=-999., resampling_method:str='nearest'):
        super().__init__(GCP_REPROJECT_OP)

        self._selected_bands_or_indices = bands

        self._lat_band = lat_band
        self._lng_band = lng_band
        self._gcp_epsg = gcp_epsg
        self._no_data = no_data

        assert resampling_method in GDAL_RESAMPLING_METHODS, f'resampling_method should be one of {GDAL_RESAMPLING_METHODS}'
        self._resampling_method = resampling_method

        assert pixel_size > 0, 'pixel_size should be greater than 0'
        self._pixel_size = pixel_size

    def __call__(self, raster:Raster, context:Context, *args):

        if not is_epsg_code_valid(self._gcp_epsg):
            raise ValueError(f'Invalid EPSG code {self._gcp_epsg}')

        # check if lat and lng bands are contained in the raster
        if self._lat_band not in raster.get_band_names() or self._lng_band not in raster.get_band_names():
            raise ValueError(f'lat_band and lng_band should be contained in the raster bands')

        _, lng_band = read_gdal_bands(raster.raw, [raster.band_to_index[self._lng_band]])
        _, lat_band = read_gdal_bands(raster.raw, [raster.band_to_index[self._lat_band]])

        min_lng, max_lng = lng_band.min(), lng_band.max()
        min_lat, max_lat = lat_band.min(), lat_band.max()

        gcp_key = str_to_hash(f'{min_lng}{max_lng}{min_lat}{max_lat}{self._gcp_epsg}')

        try:
            if gcp_key in context.cache:
                 gcp_list = context.cache[f'gcp_{gcp_key}']
            else:
                gcp_list = create_gcp(lons=lng_band, lats=lat_band)
                # todo: add to cache
        except Exception as e:
            gcp_list = create_gcp(lons=lng_band, lats=lat_band)

        resampling_method = self._resampling_method
        arr = raster.raw.ReadAsArray()
        reprojected_ds = reproject_arr_using_gcp(arr, gcp_list,
                                                 min_x=min_lng, max_x=max_lng, min_y=min_lat, max_y=max_lat,
                                                 res=self._pixel_size, resampling_method=self._resampling_method,
                                                 in_epsg=self._gcp_epsg, no_data=self._no_data)
        raster.raw = reprojected_ds

        raster = self.pre_process(raster, selected_bands_or_indices=self._selected_bands_or_indices,
                                  band_select=True)  # select bands after
        self.post_process(raster, context)

        return raster


