from typing import Union
from enum import Enum
from core.raster import ModuleError

class RasterType(Enum):
    GDAL = 'gdal'
    SNAP = 'snap'

    @classmethod
    def from_str(cls, s):
        if s == 'gdal':
            return cls.GDAL
        elif s == 'snap':
            return cls.SNAP
        else:
            raise ModuleError(s)

    def __str__(self):
        return self.value

def raster_type(s:Union[str, RasterType]) -> RasterType:
    if isinstance(s, RasterType):
        return s
    else:
        return RasterType.from_str(s)

class ProductType(Enum):
    S1 = 'S1'
    S2 = 'S2'
    UNKNOWN = 'UNKNOWN'

    @classmethod
    def from_str(cls, s):
        if s == 'S1':
            return cls.S1
        elif s == 'S2':
            return cls.S2
        elif s == 'OTHER':
            return cls.UNKNOWN
        else:
            raise ValueError(f'{s} is not a valid ProductType')

    def __str__(self):
        return self.value