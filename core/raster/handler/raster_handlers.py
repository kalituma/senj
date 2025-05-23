from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from osgeo import osr

from core.util.nc import get_band_names_nc
from core.util.gdal import create_envelope, get_raster_envelope
import warnings

if TYPE_CHECKING:
    from osgeo.gdal import Dataset
    from snappy import Product
    from osgeo.ogr import Geometry

class RasterHandler(ABC):
    @abstractmethod
    def get_band_size(self, raw) -> int:
        pass

    @abstractmethod
    def get_band_names_from_raw(self, raw) -> list[str]:
        pass

    @abstractmethod
    def proj(self, raw) -> str:
        pass
    
    @abstractmethod
    def get_tie_point_grid_names(self, raw) -> list[str]:
        pass

    @abstractmethod
    def bounds(self, raw) -> tuple[float, float, float, float]:
        pass

    @abstractmethod
    def get_envelope_geom(self, raw) -> "Geometry":
        pass

    def get_band_names_from_meta_dict(self, meta_dict:dict) -> list[str]:
        band_indices = list(range(1, len(meta_dict['index_to_band'])+1))
        return [meta_dict['index_to_band'][index] for index in band_indices]

    @abstractmethod
    def get_pixel_size(self, raw) -> float:
        pass

    @abstractmethod
    def close(self, raw) -> None:
        pass

class GdalRasterHandler(RasterHandler):

    def get_band_size(self, raw: "Dataset") -> int:
        return raw.RasterCount

    def get_band_names_from_raw(self, raw:"Dataset") -> list[str]:
        band_indices = list(range(1, raw.RasterCount+1))        
        return [f'band_{index}' for index in band_indices]

    def proj(self, raw:"Dataset") -> str:
        return raw.GetProjection()    

    def get_tie_point_grid_names(self, raw:"Dataset") -> Optional[list[str]]:        
        raise NotImplementedError("Tie point grid names not implemented for GDAL")
    
    def bounds(self, raw: "Dataset") -> tuple[float, float, float, float]:
        ulx, uly, _, _, lrx, lry, _, _= get_raster_envelope(raw)
        return ulx, uly, lrx, lry

    def get_envelope_geom(self, raw:"Dataset") -> "Geometry":        
        
        ulx, uly, urx, ury, lrx, lry, llx, lly = get_raster_envelope(raw)

        env_polygon =  create_envelope(ulx, uly, urx, ury, lrx, lry, llx, lly)
        srs = osr.SpatialReference()
        srs.ImportFromWkt(raw.GetProjectionRef())
        env_polygon.AssignSpatialReference(srs)

        return env_polygon

    def close(self, raw:"Dataset") -> None:
        raw = None

    def get_pixel_size(self, raw:"Dataset") -> float:
        gt = raw.GetGeoTransform()
        return gt[1]

class SnapRasterHandler(RasterHandler):
    def get_band_size(self, raw:"Product") -> int:
        return raw.getNumBands()

    def get_band_names_from_raw(self, raw:"Product") -> list[str]:
        return list(raw.getBandNames())
    
    def proj(self, raw:"Product") -> str:
        return raw.getSceneCRS().toWKT()

    def get_tie_point_grid_names(self, raw:"Product") -> Optional[list[str]]:
        grid_names =  raw.getTiePointGridNames()
        if len(grid_names) > 0:
            return grid_names

    def bounds(self, raw: "Product") -> list[float]:
        raise NotImplementedError("Envelope not implemented for SNAP")

    def get_envelope_geom(self, raw:"Product"):
        raise NotImplementedError("Envelope not implemented for SNAP")
    
    def close(self, raw:"Product") -> None:
        raw.dispose()

    def get_pixel_size(self, raw:"Product") -> float:
        raise NotImplementedError("Pixel size not implemented for SNAP")


class NCRasterHandler(RasterHandler):
    def get_band_size(self, raw) -> int:        
        return len(get_band_names_nc(raw))
    
    def get_band_names_from_raw(self, raw) -> list[str]:
        return get_band_names_nc(raw)
    
    def proj(self, raw) -> str:
        raise NotImplementedError("Projection not implemented for NetCDF")
    
    def get_tie_point_grid_names(self, raw) -> Optional[list[str]]:        
        raise NotImplementedError("Tie point grid names not implemented for NetCDF")
    
    def bounds(self, raw) -> list[float]:
        raise NotImplementedError("Envelope not implemented for NetCDF")
    
    def get_envelope_geom(self, raw):
        raise NotImplementedError("Envelope not implemented for NetCDF")
    
    def close(self, raw) -> None:
        raw = None

    def get_pixel_size(self, raw) -> float:
        raise NotImplementedError("Pixel size not implemented for NetCDF")
