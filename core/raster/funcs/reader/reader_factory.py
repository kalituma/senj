from pathlib import Path
from typing import Dict, Type, List, AnyStr, Tuple
from core.util import ProductType, ModuleType
from core.raster.funcs.reader import BaseRasterReader
from core.raster.funcs.reader import (
    TifGdalReader,
    GribGdalReader,
    NcReader,
    SnapReader,
    SafeGdalReader
)

class ReaderFactory:
    _reader_map : Dict[Tuple[ModuleType, Tuple[AnyStr]], Type[BaseRasterReader]] = {
        (ModuleType.SNAP, ('safe', 'dim', 'tif')): SnapReader,
        (ModuleType.GDAL, ('safe',)): SafeGdalReader,
        (ModuleType.GDAL, ('gb2',)): GribGdalReader,
        (ModuleType.NETCDF, ('nc',)): NcReader,
        (ModuleType.GDAL, ('tif', 'xml', 'json')): TifGdalReader
    }

    @classmethod
    def get_reader(cls, file_path: str, module_type: ModuleType) -> BaseRasterReader:
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        
        for (mod_type, extensions), reader_cls in cls._reader_map.items():
            if module_type == mod_type and file_ext in extensions:
                return reader_cls()
        
        raise ValueError(f"not supported file extension: {file_ext} (module: {module_type})")