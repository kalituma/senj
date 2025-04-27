from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from core.util.nc import get_band_names_nc

if TYPE_CHECKING:
    from osgeo.gdal import Dataset
    from snappy import Product

class ModuleTypeHandler(ABC):
    @abstractmethod
    def get_band_size(self, raw) -> int:
        pass

    @abstractmethod
    def get_band_names(self, raw) -> list[str]:
        pass

    @abstractmethod
    def proj(self, raw) -> str:
        pass
    
    @abstractmethod
    def get_tie_point_grid_names(self, raw) -> list[str]:
        pass

    @abstractmethod
    def close(self, raw) -> None:
        pass

class GdalRasterHandler(ModuleTypeHandler):
    def get_band_size(self, raw: "Dataset") -> int:
        return raw.RasterCount

    def get_band_names(self, raw:"Dataset", meta_dict:Optional[dict] = None) -> list[str]:
        band_indices = list(range(1, raw.RasterCount+1))
        if meta_dict is not None:
            try:
                return [meta_dict['index_to_band'][index-1] for index in band_indices]
            except Exception:
                pass
        return [f'band_{index}' for index in band_indices]

    def proj(self, raw:"Dataset") -> str:
        return raw.GetProjection()    

    def close(self, raw:"Dataset") -> None:
        raw = None

class SnapRasterHandler(ModuleTypeHandler):
    def get_band_size(self, raw:"Product") -> int:
        return raw.getNumBands()

    def get_band_names(self, raw:"Product", meta_dict:Optional[dict] = None) -> list[str]:
        return list(raw.getBandNames())
    
    def proj(self, raw:"Product") -> str:
        return raw.getSceneCRS().toWKT()

    def get_tie_point_grid_names(self, raw:"Product") -> Optional[list[str]]:
        grid_names =  raw.getTiePointGridNames()
        if len(grid_names) > 0:
            return grid_names

    def close(self, raw:"Product") -> None:
        raw.dispose()


class NCRasterHandler(ModuleTypeHandler):
    def get_bands_size(self, raw) -> int:        
        return len(get_band_names_nc(raw))    
    def get_band_names(self, raw, meta_dict:Optional[dict] = None) -> list[str]:
        return get_band_names_nc(raw)    
    def get_projection(self, raw) -> str:
        raise NotImplementedError("Projection not implemented for NetCDF")
    
    def close(self, raw) -> None:
        raw = None