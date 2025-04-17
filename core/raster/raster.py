from typing import Union, TypeVar, TYPE_CHECKING, Dict
import warnings
from pathlib import Path

from core.util import ProductType, ModuleType, check_raw_type
from core.util.nc import get_band_names_nc
from core.raster import RasterMeta


if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo.gdal import Dataset
    from core.raster.handlers import ModuleTypeHandler, GdalRasterHandler, SnapRasterHandler, NCRasterHandler


T = TypeVar('T', bound='Raster')

class Raster(RasterMeta):
    _module_handlers: Dict[ModuleType, "ModuleTypeHandler"] = {
        ModuleType.GDAL: "GdalRasterHandler",
        ModuleType.SNAP: "SnapRasterHandler",
        ModuleType.NETCDF: "NCRasterHandler"
    }

    def __init__(self, path:str=None):

        super().__init__()

        self._module_type:ModuleType = None
        self._path:str = path
        # self._selected_bands:list[Union[str, int]] = band_names

        self._raw:Union["Product", "Dataset"] = None

        self._bands_data:dict = None
        self._product_type:ProductType = ProductType.UNKNOWN
        self._is_band_cached:bool = False
        self._raster_from:str = ''

        if not Path(path).exists():
            raise FileNotFoundError(f'{path} does not exist')

    
    @property
    def handler(self) -> "ModuleTypeHandler":
        if not self.module_type:
            raise ValueError('Module type is not set')
        
        if self.module_type not in self._module_handlers:
            raise ValueError(f'Module type {self.module_type} is not supported')

        return self._module_handlers[self.module_type]

    @staticmethod
    def from_raster(raster:T, **kwargs):
        new_raster = Raster(raster.path)

        for key, value in vars(raster).items():
            if key in ['op_history', '_module_type', '_path', '_product_type']:
                setattr(new_raster, key, value)
            else:
                continue

        for key, value in kwargs.items():
            setattr(new_raster, key, value)

        return new_raster

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

    def get_band_names(self) -> list[str]:

        # priority : 1. map 2. meta 3. raw
        # before getting band names by this function, meta_dict should be always updated.

        if self.initialized:
            return list(self._index_to_band.values())
        return self.handler.get_band_names(self.raw, self.meta_dict)
    
    def get_band_names_from_raw(self) -> list[str]:
        return self.handler.get_band_names(self.raw)

    def get_tie_point_grid_names(self) -> Union[list[str], None]:
        return self.handler.get_tie_point_grid_names(self.raw)

    def del_bands_cache(self):
        self.bands = None
        self.is_band_cached = False

    def close(self):
        super().close()
        self.handler.close(self.raw)
        self.is_band_cached = False

    def cached_bands_have_same_shape(self) -> bool:
        cached_band_names = list(self.bands.keys())
        return all([self.bands[band_name]['value'].shape == self.bands[cached_band_names[0]]['value'].shape for band_name in cached_band_names])

    def convert_to_have_same_dtype(self) -> None:
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
    
    def reorder_bands(self, band_names:list[str]) -> None:
        self.bands = {band_name: self.bands[band_name] for band_name in band_names}

    def proj(self) -> str:
        assert self.raw is not None, 'For getting projection, raster object must have raw data.'
        return self.handler.proj(self.raw)

    @property
    def bands(self):
        return self._bands_data

    @bands.setter
    def bands(self, bands):
        self._bands_data = bands

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def raw(self):
        return self._raw

    @raw.setter
    def raw(self, raw:Union["Product", "Dataset"]):
        self._raw = raw
        if raw is not None:
            self._module_type = check_raw_type(raw)

    @property
    def module_type(self):
        return self._module_type

    @module_type.setter
    def module_type(self, module_type):
        if isinstance(module_type, str):
            self._module_type = ModuleType.from_str(module_type)
        else:
            self._module_type = module_type

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

    def get_cached_band_names(self) -> Union[list[str], None]:
        if self._bands_data:
            return list(self._bands_data.keys())
        else:
            return None