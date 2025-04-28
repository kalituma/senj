from abc import ABC, abstractmethod
from pathlib import Path

from core.util import ModuleType
from core.raster import Raster
from core.raster.funcs.adapter import SnapRasterAdapter, GdalRasterAdapter
from core.raster.funcs.writer.writer_strategy import SnapTifStrategy, SnapDimStrategy, GdalTifStrategy

class BaseWriter(ABC):
    def __init__(self, raster:Raster):
        self._raster = raster
        self._format_strategies = {}
        self._initialize_strategies()
        
    @property
    def raster(self):
        return self._raster
    
    @raster.setter
    def raster(self, raster:Raster):
        self._raster = raster

    @abstractmethod
    def _initialize_strategies(self) -> None:
        pass
    
    def write_meta(self, path: str) -> None:
        ext = Path(path).suffix.lower()
        if ext in self._format_strategies:
            self._format_strategies[ext].write_meta(self, self.raster, path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    
    def write(self, path: str) -> None:
        ext = Path(path).suffix.lower()
        if ext in self._format_strategies:
            self._format_strategies[ext].write(self, self.raster, path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

class SnapWriter(BaseWriter, SnapRasterAdapter):

    def _initialize_strategies(self) -> None:
        self._format_strategies = {
            '.tif': SnapTifStrategy(),
            '.dim': SnapDimStrategy()
        }

class GdalWriter(BaseWriter, GdalRasterAdapter):
    def _initialize_strategies(self) -> None:
        self._format_strategies = {
            '.tif': GdalTifStrategy()
        }


def get_writer(raster: Raster) -> BaseWriter:
    if raster.module_type == ModuleType.SNAP:
        return SnapWriter(raster)
    elif raster.module_type == ModuleType.GDAL:
        return GdalWriter(raster)
    else:
        raise ValueError(f"Unsupported module type: {raster.module_type}")