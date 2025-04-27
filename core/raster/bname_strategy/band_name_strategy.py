from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.raster.raster import Raster

class BandNameStrategy(ABC):
    @abstractmethod
    def get_band_names(self, raster:"Raster") -> list[str]:
        pass

class DefaultBandNameStrategy(BandNameStrategy):
    def get_band_names(self, raster:"Raster") -> list[str]:
        # 1. map
        if raster.initialized:
            return list(raster.index_to_band.values())
        # 2. meta
        if raster.has_meta_band_map():
            return raster.handler.get_band_names_from_meta_dict(raster.meta_dict)
        # 3. raw
        if raster.raw is not None:
            return raster.handler.get_band_names_from_raw(raster.raw)

        raise ValueError('Cannot find band names')

class MapBandNameStrategy(BandNameStrategy):
    def get_band_names(self, raster:"Raster") -> list[str]:
        if raster.initialized:
            return list(raster.index_to_band.values())
        raise ValueError('Raster is not initialized')
    
class MetaBandNameStrategy(BandNameStrategy):
    def get_band_names(self, raster:"Raster") -> list[str]:
        if raster.has_meta_band_map():
            return raster.handler.get_band_names_from_meta_dict(raster.meta_dict)
        raise ValueError('Meta band map is not initialized')
    
class RawBandNameStrategy(BandNameStrategy):
    def get_band_names(self, raster:"Raster") -> list[str]:
        if raster.raw is not None:
            return raster.handler.get_band_names_from_raw(raster.raw)
        raise ValueError('Raster has no raw data')
    
    
class BandNameStrategyFactory:
    _strategies = {
        'default': DefaultBandNameStrategy(),
        'map': MapBandNameStrategy(),
        'meta': MetaBandNameStrategy(),
        'raw': RawBandNameStrategy()
    }

    @classmethod
    def get_band_name_strategy(cls, strategy_name:str='default') -> BandNameStrategy:
        if strategy_name not in cls._strategies:
            raise ValueError(f'Invalid strategy name: {strategy_name}')
        return cls._strategies[strategy_name]