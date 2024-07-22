from typing import TYPE_CHECKING
from core.operations import Op
from core.operations import OPERATIONS, SUBSET_OP
from core.raster import Raster, RasterType
from core.util import region_to_wkt
from core.raster.gdal_module import make_transform, create_geom
from core.raster.gpf_module import subset_gpf

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SUBSET_OP)
class Subset(Op):
    def __init__(self, bounds:list[float]=None, epsg:int=None, bbox:list=None, bandNames:list[str]=None, tiePointGridNames:list[str]=None, copyMetadata:bool=True):
        super().__init__(SUBSET_OP)

        is_geo = True

        self.subset_params = {
            'bandNames': bandNames,
            'tiePointGridNames': tiePointGridNames,
            'copyMetadata': copyMetadata
        }
        # bounds = [ul_x, ul_y, lr_x, lr_y]
        if bounds:
            assert not bbox, 'Either bounds or bbox should be provided'
            assert len(bounds) == 4, 'bounds should have 4(min_x, min_y, max_x, max_y) elements'
            if not epsg:
                epsg = 4326
            is_geo = True

        if bbox:
            assert not bounds, 'Either bounds or bbox should be provided'
            assert len(bbox) == 4, 'bbox should have 4(x,y,w,h) elements'
            assert not epsg, 'epsg should not be provided'
            is_geo = False

        if is_geo:
            self._epsg = epsg
            self._bounds_wkt = region_to_wkt(bounds)

            if epsg != 4326:
                geom = create_geom(self._bounds_wkt)
                transformer = make_transform(epsg, 4326)
                self._bounds_wkt = geom.Transform(transformer).ExportToWkt()

            self.subset_params['geoRegion'] = self._bounds_wkt

        else:
            self._epsg = None
            self._bounds_wkt = None

            self.subset_params['region'] = bbox

    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if not self.subset_params['bandNames']:
            self.subset_params['bandNames'] = raster.get_band_names()

        if raster.module_type == RasterType.SNAP:
            if not self.subset_params['tiePointGridNames']:
                tie_points = raster.get_tie_point_grid_names()
                if tie_points:
                    self.subset_params['tiePointGridNames'] = tie_points
                else:
                    del self.subset_params['tiePointGridNames']

            raster.raw = subset_gpf(raster.raw, self.subset_params)

        # elif raster.module_type == RasterType.GDAL:
        #
        #     if True:
        #         # build params
        #         pass
        #     else:
        #         # execute gdal_warp
        #         pass
            # raster.raw = raster.raw.subset(self._bounds_wkt, self.subset_params['bandNames'])

        raster = self.post_process(raster, context)
        return raster