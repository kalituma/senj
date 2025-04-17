from pathlib import Path
from typing import Dict, Type, List, AnyStr, Tuple
from core.util import ProductType, ModuleType
from core.raster.funcs.reader import BaseReader
from core.raster.funcs.reader import (
    TifGdalReader,
    GribGdalReader,
    NcReader,
    SafeSnapReader,
    SafeGdalReader
)

class ReaderFactory:
    _reader_map : Dict[Tuple[ModuleType, Tuple[AnyStr]], Type[BaseReader]] = {
        (ModuleType.SNAP, ('safe', 'dim')): SafeSnapReader,
        (ModuleType.GDAL, ('safe',)): SafeGdalReader,
        (ModuleType.GDAL, ('gb2',)): GribGdalReader,
        (ModuleType.GDAL, ('nc',)): NcReader,
        (ModuleType.GDAL, ('tif', 'xml', 'json')): TifGdalReader        
    }

    @classmethod
    def get_reader(cls, file_path: str, module_type: ModuleType) -> BaseReader:
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        
        for (mod_type, extensions), reader_cls in cls._reader_map.items():
            if module_type == mod_type and file_ext in extensions:
                return reader_cls(file_path)
        
        raise ValueError(f"not supported file extension: {file_ext} (module: {module_type})")