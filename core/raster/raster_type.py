from core.util.errors import ModuleError
from typing import Union
from enum import Enum


class RasterType(Enum):
    GDAL = 'gdal'
    SNAP = 'snap'

    @classmethod
    def from_str(cls, s):
        target = s.lower()
        if target == 'gdal':
            return cls.GDAL
        elif target == 'snap':
            return cls.SNAP
        else:
            raise ModuleError(s, available_modules=[str(cls.GDAL), str(cls.SNAP)])

    def __str__(self):
        return self.value

def raster_type(s:Union[str, RasterType]) -> RasterType:
    if isinstance(s, RasterType):
        return s
    else:
        return RasterType.from_str(s)