from abc import ABC, abstractmethod
import warnings

class RasterMeta(ABC):
    def __init__(self):
        self._meta_dict:dict = None
        self._index_to_band:dict = None
        self._band_to_index:dict = None
        self.op_history: list = []

    @property
    def initialized(self) -> bool:
        return self._index_to_band is not None and self._band_to_index is not None
    
    @property
    def meta_dict(self):
        return self._meta_dict

    @meta_dict.setter
    def meta_dict(self, meta_dict):
        self._meta_dict = meta_dict

    def has_meta_dict(self):
        return self._meta_dict is not None
    
    def has_meta_band_map(self):
        if not self.has_meta_dict:
            warnings.warn('Meta dict is not initialized')
            return False        
        return 'index_to_band' in self._meta_dict and 'band_to_index' in self._meta_dict
    
    @property
    def index_to_band(self):
        return self._index_to_band.copy() if self._index_to_band is not None else None
    
    @index_to_band.setter
    def index_to_band(self, index_to_band):
        self._index_to_band = index_to_band

    @property
    def band_to_index(self):
        return self._band_to_index.copy() if self._band_to_index is not None else None
    
    @band_to_index.setter
    def band_to_index(self, band_to_index):
        self._band_to_index = band_to_index

    def get_bname_as_list(self):
        return list(self._index_to_band.values())
       
    @abstractmethod
    def get_band_names(self):
        pass

    # def init_band_map_raw(self, bnames):
    #     assert self._index_to_band is None and self._band_to_index is None, 'Band map should be initialized only once.'
    #
    #     if self.meta_dict:
    #         self.meta_dict['index_to_band'], self.meta_dict['band_to_index'] = self._produce_band_map(bnames)
    #         self.copy_band_map_from_meta()
    #     else:
    #         self._index_to_band, self._band_to_index = self._produce_band_map(bnames)
    #
    # def update_index_bnames(self, bnames=None):
    #     all_names = self.get_band_names()
    #
    #     if self._index_to_band is None and self._band_to_index is None:
    #         if self.meta_dict:
    #             if 'index_to_band' in self.meta_dict and 'band_to_index' in self.meta_dict:
    #                 self.copy_band_map_from_meta()
    #             else:
    #                 self.init_band_map_raw(all_names)
    #         else:
    #             if bnames is not None:
    #                 self.update_band_map(bnames)
    #             else:
    #                 self.init_band_map_raw(all_names)
    #     else:
    #         if self._meta_dict is not None:
    #             self.copy_band_map_from_meta()
    #         else:
    #             assert bnames is not None, 'bnames should be provided'
    #             self.update_band_map(bnames)
    #
    #     return self

    def index_to_band_name(self, indices:list[int]) -> list[str]:
        return [self._index_to_band[i] for i in indices]

    def band_name_to_index(self, band_names:list[str]) -> list[int]:
        return [self._band_to_index[b] for b in band_names]

    # def update_band_map(self, bnames):
    #     self._index_to_band, self._band_to_index = self._produce_band_map(bnames)

    # def update_band_map_to_meta(self, bnames):
    #     self.meta_dict['index_to_band'], self.meta_dict['band_to_index'] = self._produce_band_map(bnames)

    # def copy_band_map_from_meta(self):
    #     self._index_to_band, self._band_to_index = self.meta_dict['index_to_band'], self.meta_dict['band_to_index']

    # def copy_band_map_to_meta(self):
    #     self.meta_dict['index_to_band'], self.meta_dict['band_to_index'] = self._index_to_band, self._band_to_index

    def _produce_band_map(self, band_names:list[str]):
        return {i+1: b for i, b in enumerate(band_names)}, {b: i+1 for i, b in enumerate(band_names)}

    def _get_band_names_from_meta(self, indices:list) -> list[str]:
        try:
            return [self.meta_dict['index_to_band'][index-1] for index in indices]
        except Exception as e:
            return [f'band_{index}' for index in indices]

    def add_history(self, history):
        self.op_history.append(history)

    def close(self):
        self.bands = None
        self.meta_dict = None

