from typing import Union, TypeVar
from osgeo.gdal import Dataset
from esa_snappy import Product
from pathlib import Path

from core.raster import RasterType, ProductType
T = TypeVar('T', bound='Raster')

class Raster:

    def __init__(self, path:str=None, band_names:list[Union[str, int]]=None):

        self._module_type:RasterType = None
        self._path:str = path
        self._selected_bands:list[Union[str, int]] = band_names

        self._raw:Union[ProductType, Dataset] = None
        self._meta_dict:dict = None

        self._index_to_band:dict = None
        self._band_to_index:dict = None

        self._bands_data:dict = None
        self._product_type:ProductType = ProductType.UNKNOWN
        self._is_band_cached:bool = False

        self._warp_options:dict = None

        self.op_history:list = []

        if not Path(path).exists():
            raise FileNotFoundError(f'{path} does not exist')

    @staticmethod
    def from_raster(raster:T, **kwargs):
        new_raster = Raster(raster.path)

        for key, value in vars(raster).items():
            if key in ['op_history', '_warp_options']:
                if value:
                    setattr(new_raster, key, value.copy())
            elif key in ['_module_type', '_path', '_product_type']:
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

    def _init_band_map(self):
        bnames = self.get_band_names()

        if self.meta_dict:
            self.meta_dict['index_to_band'] = {i+1: b for i, b in enumerate(bnames)}
            self.meta_dict['band_to_index'] = {b: i+1 for i, b in enumerate(bnames)}
            self._update_band_map_from_meta()
        else:
            self._index_to_band = {i + 1: b for i, b in enumerate(bnames)}
            self._band_to_index = {b: i + 1 for i, b in enumerate(bnames)}

    def _update_band_map_from_meta(self):
        self._index_to_band = self.meta_dict['index_to_band']
        self._band_to_index = self.meta_dict['band_to_index']

    def get_band_names(self) -> list[str]:
        # before call this function, meta_dict should be updated.

        if self.module_type == RasterType.GDAL:
            band_indices = list(range(1, self.raw.RasterCount+1))
            bnames = self._get_band_names_from_meta(band_indices)

        elif self.module_type == RasterType.SNAP:
            bnames = list(self.raw.getBandNames())
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')

        return bnames

    def _get_band_names_from_meta(self, indices:list) -> list[str]:
        try:
            return [self.meta_dict['index_to_band'][index-1] for index in indices]
        except Exception as e:
            return [f'band_{index}' for index in indices]

    def indices_to_band_names(self, indices:list[int]) -> list[str]:
        return [self._index_to_band[i] for i in indices]

    def band_names_to_indices(self, band_names:list[str]) -> list[int]:
        return [self._band_to_index[b] for b in band_names]

    def get_tie_point_grid_names(self) -> Union[list[str], None]:
        if self.module_type == RasterType.SNAP:
            grid_names = self.raw.getTiePointGridNames()
            if len(grid_names) > 0:
                return grid_names
        return None

    def add_history(self, history):
        self.op_history.append(history)

    def del_bands_cache(self):
        self.bands = None
        self.is_band_cached = False

    def close(self):
        self.bands = None
        self.meta_dict = None

        if self.module_type == RasterType.GDAL:
            self.raw = None
        elif self.module_type == RasterType.SNAP:
            self.raw.dispose()

        self.is_band_cached = False

    def width(self, band_name:str):
        return self.bands[band_name].shape[1]

    def height(self, band_name:str):
        return self.bands[band_name].shape[0]

    def cached_bands_have_same_shape(self):
        return all([self.bands[band].shape == self.bands[self.selected_bands[0]].shape for band in self.selected_bands])

    def proj(self):
        assert self.raw is not None, 'For getting projection, raster object must have raw data.'

        if self.module_type == RasterType.GDAL:
            return self.raw.GetProjection()
        elif self.module_type == RasterType.SNAP:
            return self.raw.getSceneCRS().toWKT()

    @property
    def selected_bands(self):
        return self._selected_bands

    @selected_bands.setter
    def selected_bands(self, bands):
        self._selected_bands = bands

    @property
    def bands(self):
        return self._bands_data

    @bands.setter
    def bands(self, bands):
        self._bands_data = bands

    @property
    def meta_dict(self):
        return self._meta_dict

    @meta_dict.setter
    def meta_dict(self, meta_dict):
        self._meta_dict = meta_dict

        if self._index_to_band is None and self._band_to_index is None:
            self._init_band_map()
        else:
            if self._meta_dict is not None:
                self._update_band_map_from_meta()

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
    def raw(self, raw):
        self._raw = raw
        if isinstance(raw, Dataset):
            self._module_type = RasterType.GDAL
        elif isinstance(raw, Product):
            self._module_type = RasterType.SNAP
        else:
            self._module_type = None

    @property
    def module_type(self):
        return self._module_type

    @module_type.setter
    def module_type(self, module_type):
        if isinstance(module_type, str):
            self._module_type = RasterType.from_str(module_type)
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
