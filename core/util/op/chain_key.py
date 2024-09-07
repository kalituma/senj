from enum import Enum

class CHAIN_KEY(Enum):
    NOTSET = 'none'
    WARP = 'warp'

    @classmethod
    def from_str(cls, s):
        s = s.lower()
        if s == 'warp':
            return cls.WARP
        elif s == 'notset':
            return cls.NOTSET
        else:
            raise ValueError(f"Unknown CHAIN_KEY: {s}")