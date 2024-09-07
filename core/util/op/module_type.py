from enum import Enum

GDAL_OPS = ['gdal']

# snap -> cached -> snap
# gdal -> cached -> gdal
# snap -> convert -> gdal
# gdal -> convert -> snap
class MODULE_TYPE(Enum):
    NOTSET = 'none'
    GDAL = 'gdal'
    SNAP = 'snap'
    CONVERT = 'convert'

    @classmethod
    def from_str(cls, s):
        s = s.lower()
        if s == 'gdal':
            return cls.GDAL
        elif s == 'snap':
            return cls.SNAP
        elif s == 'convert':
            return cls.CONVERT
        elif s == 'notset':
            return cls.NOTSET
        else:
            raise ValueError(f"Unknown OP_TYPE: {s}")

    def __invert__(self):
        if self == self.GDAL:
            return self.SNAP
        elif self == self.SNAP:
            return self.GDAL
        else:
            raise ValueError(f"Cannot invert OP_TYPE: {self}")
