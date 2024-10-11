from typing import Union, TypeVar, TYPE_CHECKING

from pathlib import Path

from core.util import ProductType, ModuleType, check_raw_type
from core.util.nc import get_band_names_nc
from core.raster import RasterMeta


if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo.gdal import Dataset


T = TypeVar('T', bound='Raster')

class Raster(RasterMeta):
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
        if self.module_type == ModuleType.GDAL:
            return self.raw.RasterCount
        elif self.module_type == ModuleType.SNAP:
            return self.raw.getNumBands()
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')

    def get_band_names(self) -> list[str]:

        # priority : 1. map 2. meta 3. raw
        # before getting band names by this function, meta_dict should be always updated.

        if self._index_to_band is not None and self._band_to_index is not None:
            return list(self._index_to_band.values())

        if self.module_type == ModuleType.GDAL:
            band_indices = list(range(1, self.raw.RasterCount+1))
            bnames = self._get_band_names_from_meta(band_indices) # from meta if exists else create by index
        elif self.module_type == ModuleType.SNAP:
            bnames = list(self.raw.getBandNames())
        elif self.module_type == ModuleType.NETCDF:
            bnames = get_band_names_nc(self.raw)
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')

        return bnames

    def get_tie_point_grid_names(self) -> Union[list[str], None]:
        if self.module_type == ModuleType.SNAP:
            grid_names = self.raw.getTiePointGridNames()
            if len(grid_names) > 0:
                return grid_names
        return None

    def del_bands_cache(self):
        self.bands = None
        self.is_band_cached = False

    def close(self):
        super().close()

        if self.module_type == ModuleType.GDAL:
            self.raw = None
        elif self.module_type == ModuleType.SNAP:
            self.raw.dispose()

        self.is_band_cached = False

    def cached_bands_have_same_shape(self):
        cached_band_names = list(self.bands.keys())
        return all([self.bands[band_name]['value'].shape == self.bands[cached_band_names[0]]['value'].shape for band_name in cached_band_names])

    def proj(self) -> str:
        assert self.raw is not None, 'For getting projection, raster object must have raw data.'

        if self.module_type == ModuleType.GDAL:
            return self.raw.GetProjection()
        elif self.module_type == ModuleType.SNAP:
            return self.raw.getSceneCRS().toWKT()
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')


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

    def update_index_bnames_from_raw(self):
        if self.module_type == ModuleType.SNAP:
            bnames = list(self.raw.getBandNames())
            self.update_band_map(bnames)
            if self.meta_dict:
                self.update_band_map_to_meta(bnames)

        return self