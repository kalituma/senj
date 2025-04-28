from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from core.raster import Raster
from core.util.gdal import is_bigtiff_gdal
from core.util.snap import is_bigtiff_gpf
from core.util import set_btoi_to_tif, set_btoi_to_tif_meta
from core.util.meta import write_metadata

if TYPE_CHECKING:
    from core.raster.funcs.adapter import GdalRasterAdapter, SnapRasterAdapter

class FormatStrategy(ABC):
    @abstractmethod
    def write(self, writer, raster: Raster, path: str) -> None:
        pass
    
    @abstractmethod
    def write_meta(self, writer, raster: Raster, path: str) -> None:
        pass

class GdalTifStrategy(FormatStrategy):
    def write(self, writer: "GdalRasterAdapter", raster: Raster, path: str) -> None:
        is_bigtiff = is_bigtiff_gdal(raster.raw)
        compress = is_bigtiff
        writer.write_data(raster.raw, path, is_bigtiff=is_bigtiff, compress=compress)
    
    def write_meta(self, writer, raster: Raster, path: str) -> None:
        write_metadata(raster.meta_dict, path)
        set_btoi_to_tif_meta(raster.raw, raster.band_to_index)

class SnapTifStrategy(FormatStrategy):
    def write(self, writer: "SnapRasterAdapter", raster: Raster, path: str) -> None:
        is_bigtiff = is_bigtiff_gpf(raster.raw)
        format_type = 'GeoTIFF-BigTIFF' if is_bigtiff else 'GeoTIFF'
        writer.write_data(raster.raw, path, format_type)
    
    def write_meta(self, writer, raster: Raster, path: str) -> None:
        write_metadata(raster.meta_dict, path)
        set_btoi_to_tif(path, raster.band_to_index)

class SnapDimStrategy(FormatStrategy):
    def write(self, writer: "SnapRasterAdapter", raster: Raster, path: str) -> None:
        writer.write_data(raster.raw, path, 'BEAM-DIMAP')
    
    def write_meta(self, writer, raster: Raster, path: str) -> None:
        write_metadata(raster.meta_dict, path)