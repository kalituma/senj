from typing import Union, TypeVar, TYPE_CHECKING
from osgeo.gdal import Dataset
from esa_snappy import Product
from pathlib import Path

from core.util import ProductType
from core.raster import RasterType


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

    def _init_band_map_raw(self):
        assert self._index_to_band is None and self._band_to_index is None, 'Band map should be initialized only once.'

        band_to_index = None
        if self.module_type == RasterType.GDAL:
            band_to_index = self.raw.GetMetadata('band_to_index')
            if len(band_to_index) == 0:
                band_to_index = None

        if band_to_index is None:
            bnames = self.get_band_names()
        else:
            bnames = list(band_to_index.keys())

        if self.meta_dict:
            self.meta_dict['index_to_band'], self.meta_dict['band_to_index'] = self._produce_band_map(bnames)
            self._copy_band_map_from_meta()
        else:
            self._index_to_band, self._band_to_index = self._produce_band_map(bnames)

    def update_band_map(self, bnames):
        self._index_to_band, self._band_to_index = self._produce_band_map(bnames)
    def update_band_map_to_meta(self, bnames):
        self.meta_dict['index_to_band'], self.meta_dict['band_to_index'] = self._produce_band_map(bnames)

    def _copy_band_map_from_meta(self):
        self._index_to_band = self.meta_dict['index_to_band']
        self._band_to_index = self.meta_dict['band_to_index']

    def _produce_band_map(self, band_names:list[str]):
        return {i+1: b for i, b in enumerate(band_names)}, {b: i+1 for i, b in enumerate(band_names)}

    def get_band_names(self) -> list[str]:

        # priority : 1. map 2. meta 3. raw
        # before get band names by calling this function, meta_dict should be always updated.

        if self._index_to_band is not None and self._band_to_index is not None:
            return list(self._index_to_band.values())

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

    def index_to_band_name(self, indices:list[int]) -> list[str]:
        return [self._index_to_band[i] for i in indices]

    def band_name_to_index(self, band_names:list[str]) -> list[int]:
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
        self.selected_bands = None

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
        return all([self.bands[band]['value'].shape == self.bands[self.selected_bands[0]]['value'].shape for band in self.selected_bands])

    def proj(self) -> str:
        assert self.raw is not None, 'For getting projection, raster object must have raw data.'

        if self.module_type == RasterType.GDAL:
            return self.raw.GetProjection()
        elif self.module_type == RasterType.SNAP:
            return self.raw.getSceneCRS().toWKT()
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')

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

    def get_cached_band_names(self) -> Union[list[str], None]:
        if self._bands_data:
            return list(self._bands_data)
        else:
            return None

    @property
    def meta_dict(self):
        return self._meta_dict

    @meta_dict.setter
    def meta_dict(self, meta_dict):
        self._meta_dict = meta_dict

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

    def update_index_bnames(self, bnames=None):
        if self._index_to_band is None and self._band_to_index is None:
            if self.meta_dict:
                if 'index_to_band' in self.meta_dict and 'band_to_index' in self.meta_dict:
                    self._copy_band_map_from_meta()
                else:
                    self._init_band_map_raw()
            else:
                if bnames is not None:
                    self.update_band_map(bnames)
                else:
                    self._init_band_map_raw()
        else:
            if self._meta_dict is not None:
                self._copy_band_map_from_meta()
            else:
                assert bnames is not None, 'bnames should be provided'
                self.update_band_map(bnames)

        return self

    def update_index_bnames_from_raw(self):
        if self.module_type == RasterType.SNAP:
            bnames = self.raw.getBandNames()
            self.update_band_map(bnames)
            self.update_band_map_to_meta(bnames)

        return self