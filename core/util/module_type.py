from typing import Union
from enum import Enum

from core.util.errors import ModuleError

class ModuleType(Enum):
    GDAL = 'gdal'
    SNAP = 'snap'
    NETCDF = 'netcdf'
    VECTOR = 'vector'

    @classmethod
    def from_str(cls, s):
        target = s.lower()
        if target == 'gdal':
            return cls.GDAL
        elif target == 'snap':
            return cls.SNAP
        elif target == 'netcdf':
            return cls.NETCDF
        elif target == 'vector':
            return cls.VECTOR
        else:
            raise ModuleError(s, available_modules=[str(cls.GDAL), str(cls.SNAP), str(cls.NETCDF), str(cls.VECTOR)])

    def __str__(self):
        return self.value

def module_type(s:Union[str, ModuleType]) -> ModuleType:
    if isinstance(s, ModuleType):
        return s
    else:
        return ModuleType.from_str(s)