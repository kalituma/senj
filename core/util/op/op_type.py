from enum import Enum

GDAL_OPS = ['gdal']

# snap -> cached -> snap
# gdal -> cached -> gdal
# snap -> convert -> gdal
# gdal -> convert -> snap
class OP_TYPE(Enum):
    GDAL = 'GDAL'
    SNAP = 'SNAP'
    CACHED = 'CACHED'
    CONVERT = 'CONVERT'

    @classmethod
    def from_str(cls, s):
        if s == 'GDAL':
            return cls.GDAL
        elif s == 'SNAP':
            return cls.SNAP
        elif s == 'CACHED':
            return cls.CACHED
        elif s == 'CONVERT':
            return cls.CONVERT
        else:
            raise ValueError(f"Unknown OP_TYPE: {s}")
