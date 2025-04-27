from typing import Union, TypeVar, TYPE_CHECKING, Dict, Optional
import warnings
from pathlib import Path

from core.base import GeoData
from core.util import ProductType, ModuleType
from core.raster import RasterMeta
from core.raster.handler import GdalRasterHandler, SnapRasterHandler, NCRasterHandler
from core.raster.bname_strategy import BandNameStrategyFactory

if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo.gdal import Dataset

    from core.raster.handler import RasterHandler



T = TypeVar('T', bound='Raster')

class Raster(GeoData, RasterMeta):
    _module_handlers: Dict[ModuleType, "RasterHandler"] = {
        ModuleType.GDAL: GdalRasterHandler(),
        ModuleType.SNAP: SnapRasterHandler(),
        ModuleType.NETCDF: NCRasterHandler()
    }

    def __init__(self, path:str=None):

        super().__init__()
        
        self._path:str = path
        # self._selected_bands:list[Union[str, int]] = band_names

        self._raw:Union["Product", "Dataset"] = None

        self._bands_data:dict = None
        self._product_type:ProductType = ProductType.UNKNOWN
        self._is_band_cached:bool = False
        self._raster_from:str = ''

        if not Path(path).exists():
            raise FileNotFoundError(f'{path} does not exist')

    @classmethod
    def create(cls, path:str, module_type:Optional[ModuleType]=None, product_type:Optional[ProductType]=None):
        raster = cls(path)
        if module_type is not None:
            raster.module_type = module_type
        if product_type is not None:
            raster.product_type = product_type
            
        return raster

    @staticmethod
    def from_raster(raster:T, **kwargs):
        new_raster = Raster.create(raster.path)

        for key, value in vars(raster).items():
            if key in ['op_history', '_module_type', '_path', '_product_type']:
                setattr(new_raster, key, value)
            else:
                continue

        for key, value in kwargs.items():
            setattr(new_raster, key, value)

        return new_raster

    @property
    def handler(self) -> "RasterHandler":
        if not self.module_type:
            raise ValueError('Module type is not set')
        
        if self.module_type not in self._module_handlers:
            raise ValueError(f'Module type {self.module_type} is not supported')

        return self._module_handlers[self.module_type]

    @property
    def bands(self):
        return self._bands_data

    @bands.setter
    def bands(self, bands):
        self._bands_data = bands
    
    @property
    def product_type(self):
        return self._product_type

    @product_type.setter
    def product_type(self, product_type):
        if isinstance(product_type, str):
            self._product_type = ProductType.from_str(product_type)
        else:
            self._product_type = product_type

    @property
    def is_band_cached(self):
        return self._is_band_cached

    @is_band_cached.setter
    def is_band_cached(self, is_cached):
        self._is_band_cached = is_cached

    @property
    def raster_from(self):
        return self._raster_from

    @raster_from.setter
    def raster_from(self, from_proc):
        self._raster_from = from_proc

    def __getitem__(self, item):
        return self.bands[item]

    def __setitem__(self, key, value):
        self.bands[key] = value

    def __len__(self):
        return len(self.bands)

    def __str__(self):
        return f'Raster : {self.path} processed from {self.op_history[0]} to {self.op_history[-1]}'

    def get_bands_size(self) -> int:
        return self.handler.get_band_size(self.raw)

    def get_band_names(self, b_type:str= 'default') -> list[str]:
        strategy = BandNameStrategyFactory.get_band_name_strategy(b_type)
        return strategy.get_band_names(self)


    def get_tie_point_grid_names(self) -> Union[list[str], None]:
        return self.handler.get_tie_point_grid_names(self.raw)

    def del_bands_cache(self):
        self.bands = None
        self.is_band_cached = False

    def cached_bands_have_same_shape(self) -> bool:
        cached_band_names = list(self.bands.keys())
        return all([self.bands[band_name]['value'].shape == self.bands[cached_band_names[0]]['value'].shape for band_name in cached_band_names])


    def to_have_same_dtype(self) -> None:
        cached_band_names = list(self.bands.keys())
        dtypes = [self.bands[band_name]['value'].dtype for band_name in cached_band_names]
        have_same_dtype = all([dtypes[0] == dtype for dtype in dtypes])
        if not have_same_dtype:
            # warning
            warnings.warn('Cached bands have different dtypes. Converting to the band which has the biggest byte size.')

            # change dtype of all bands to the band which has the biggest byte size
            max_dtype = max(dtypes, key=lambda x: x.itemsize)
            for band_name in cached_band_names:
                self.bands[band_name]['value'] = self.bands[band_name]['value'].astype(max_dtype)

    def reorder_bands(self, band_names:list[str], sort:bool=True) -> None:
        if sort:
            band_names.sort()
        self.bands = {band_name: self.bands[band_name] for band_name in band_names}
    
    def proj(self) -> str:
        assert self.raw is not None, 'For getting projection, raster object must have raw data.'
        return self.handler.proj(self.raw)
    


    def get_cached_band_names(self) -> Union[list[str], None]:
        if self._bands_data:
            return list(self._bands_data.keys())
        else:
            return None

    def close(self):
        super().close()
        self.handler.close(self.raw)
        self.is_band_cached = False

