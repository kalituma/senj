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
    def __init__(self, bounds:list[float], epsg:int=4326, bandNames:list[str]=None, tiePointGridNames:list[str]=None, copyMetadata:bool=True):
        super().__init__(SUBSET_OP)
        self._epsg = epsg
        self._bounds_wkt = region_to_wkt(bounds)

        if epsg != 4326:
            geom = create_geom(self._bounds_wkt)
            transformer = make_transform(epsg, 4326)
            self._bounds_wkt = geom.Transform(transformer).ExportToWkt()


        self.subset_params = {
            'bandNames': bandNames,
            'tiePointGridNames': tiePointGridNames,
            'geoRegion': self._bounds_wkt,
            'copyMetadata': copyMetadata
        }

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

        elif raster.module_type == RasterType.GDAL:

            if True:
                # build params
                pass
            else:
                # execute gdal_warp
                pass
            # raster.raw = raster.raw.subset(self._bounds_wkt, self.subset_params['bandNames'])

        raster = self.post_process(raster, context)
        return raster