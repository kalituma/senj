from enum import Enum

class ProductType(Enum):
    S1 = 'Sentinel-1'
    S2 = 'Sentinel-2'
    WV = 'WorldView'
    PS = 'PlanetScope'
    K3 = 'Kompsat3'
    CP = 'Capella'
    CA = 'CAS500'    
    GK2A = 'GK2A'
    LDAPS = 'LDAPS'

    GOCI_CDOM = 'GOCI_CDOM'
    GOCI_AC = 'GOCI_AC'
    SMAP = 'SMAP'
    KHOA_SST = 'KHOA_SST'
    

    UNKNOWN = 'UNKNOWN'

    @classmethod
    def from_str(cls, s):
        if s == 'Sentinel-1':
            return cls.S1
        elif s == 'Sentinel-2':
            return cls.S2
        elif s == 'WorldView':
            return cls.WV
        elif s == 'PlanetScope':
            return cls.PS
        elif s == 'Kompsat3':
            return cls.K3
        elif s == 'Capella':
            return cls.CP
        elif s == 'CAD500':
            return cls.CA
        elif s == 'GOCI_CDOM':
            return cls.GOCI_CDOM
        elif s == 'GOCI_AC':
            return cls.GOCI_AC
        elif s == 'SMAP':
            return cls.SMAP
        elif s == 'KHOA_SST':
            return cls.KHOA_SST
        elif s == 'OTHER':
            return cls.UNKNOWN
        else:
            raise ValueError(f'{s} is not a valid ProductType')

    def __str__(self):
        return self.value