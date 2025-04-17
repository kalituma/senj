from enum import Enum, auto
from typing import Dict, Set, Callable

from core.raster import RasterMeta

class BandMapEvent(Enum):
    INITIALIZED = auto()
    UPDATED = auto()

class Observable:
    def __init__(self):
        self._observers: Dict[Enum,Set[Callable]] = {}

    def add_observer(self, event_type:Enum, observer:Callable) -> None:
        if event_type not in self._observers:
            self._observers[event_type] = set()
        self._observers[event_type].add(observer)

    def remove_observer(self, event_type:Enum, observer:Callable) -> None:
        if event_type in self._observers:
            self._observers[event_type].discard(observer)

    def notify_observers(self, event_type:Enum, *args, **kwargs) -> None:
        if event_type in self._observers:
            for observer in self._observers[event_type]:
                observer(*args, **kwargs)


class BandMapper(Observable):
    def __init__(self, raster : RasterMeta):
        super().__init__()
        self.raster = raster
    
    def is_initialized(self) -> bool:
        return self.raster.initialized
    
    def initialize_from_names(self, band_names:list[str]):
        assert not self.is_initialized, "BandMapper is already initialized"        
        self.raster.index_to_band, self.raster.band_to_index = self.produce_band_map(band_names)
        self.notify_observers(BandMapEvent.INITIALIZED)

    def produce_band_map(self, band_names:list[str]):
        return {i+1: b for i, b in enumerate(band_names)}, {b: i+1 for i, b in enumerate(band_names)}    
    
    def update_band_map(self, band_names:list[str]):
        self.raster.index_to_band, self.raster.band_to_index = self.produce_band_map(band_names)
        self.notify_observers(BandMapEvent.UPDATED)

    def copy_from_meta(self):
        if self.raster.has_meta_band_map():            
            index_to_band = {int(k): v for k, v in self.raster.meta_dict['index_to_band'].items()}
            band_to_index = {k: int(v) for k, v in self.raster.meta_dict['band_to_index'].items()}
            self.raster.index_to_band = index_to_band
            self.raster.band_to_index = band_to_index

    def copy_to_meta(self):
        if self.raster.has_meta_dict:
            self.raster.meta_dict['index_to_band'] = self.raster.index_to_band
            self.raster.meta_dict['band_to_index'] = self.raster.band_to_index
    