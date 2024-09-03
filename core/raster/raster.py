from typing import Union, TypeVar, TYPE_CHECKING
from osgeo.gdal import Dataset
from esa_snappy import Product
from pathlib import Path

from core.util import ProductType
from core.raster import RasterType, RasterMeta


T = TypeVar('T', bound='Raster')

class Raster(RasterMeta):
    def __init__(self, path:str=None):

        super().__init__()

        self._module_type:RasterType = None
        self._path:str = path
        # self._selected_bands:list[Union[str, int]] = band_names

        self._raw:Union[ProductType, Dataset] = None

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
        if self.module_type == RasterType.GDAL:
            return self.raw.RasterCount
        elif self.module_type == RasterType.SNAP:
            return self.raw.getNumBands()
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')

    def get_band_names(self) -> list[str]:

        # priority : 1. map 2. meta 3. raw
        # before getting band names by this function, meta_dict should be always updated.

        if self._index_to_band is not None and self._band_to_index is not None:
            return list(self._index_to_band.values())

        if self.module_type == RasterType.GDAL:
            band_indices = list(range(1, self.raw.RasterCount+1))
            bnames = self._get_band_names_from_meta(band_indices) # from meta if exists else create by index
        elif self.module_type == RasterType.SNAP:
            bnames = list(self.raw.getBandNames())
        else:
            raise NotImplementedError(f'Raster type {self.module_type.__str__()} is not implemented')

        return bnames

    def get_tie_point_grid_names(self) -> Union[list[str], None]:
        if self.module_type == RasterType.SNAP:
            grid_names = self.raw.getTiePointGridNames()
            if len(grid_names) > 0:
                return grid_names
        return None

    def del_bands_cache(self):
        self.bands = None
        self.is_band_cached = False

    def close(self):
        super().close()

        if self.module_type == RasterType.GDAL:
            self.raw = None
        elif self.module_type == RasterType.SNAP:
            self.raw.dispose()

        self.is_band_cached = False

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

    # @property
    # def selected_bands(self):
    #     return self._selected_bands
    #
    # @selected_bands.setter
    # def selected_bands(self, bands):
    #     self._selected_bands = bands

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
        if self.module_type == RasterType.SNAP:
            bnames = self.raw.getBandNames()
            self.update_band_map(bnames)
            self.update_band_map_to_meta(bnames)

        return self