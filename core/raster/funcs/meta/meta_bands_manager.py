from typing import Optional
from core.raster import RasterMeta
from core.raster.funcs.meta import BandMapper, BandMapEvent

def _diff_bnames(bnames1: Optional[list[str]], bnames2: Optional[list[str]]) -> bool:
    if bnames1 is None or bnames2 is None:
        return False
    return set(bnames1) != set(bnames2)

class MetaBandsManager:
    def __init__(self, raster : RasterMeta):
        self._raster = raster
        self._band_mapper = BandMapper(self.raster)
        self._setup_event_listners()

    @property
    def raster(self):
        return self._raster
    
    @property
    def band_mapper(self):
        return self._band_mapper
    
    def has_meta_dict(self):
        return self.raster.has_meta_dict()
    
    def has_meta_band_map(self):
        return self.raster.has_meta_band_map()
    
    def _setup_event_listners(self):
        self.band_mapper.add_observer(BandMapEvent.INITIALIZED, self.band_mapper.copy_to_meta)
        self.band_mapper.add_observer(BandMapEvent.UPDATED, self.band_mapper.copy_to_meta)    
    
    def update_band_mapping(self, bnames: Optional[list[str]] = None) -> None:
        strategy = self._determine_band_mapping_strategy(bnames)
        self._execute_band_mapping_strategy(strategy, bnames)  

    def _determine_band_mapping_strategy(self, in_bnames: Optional[list[str]] = None) -> str:

        is_bnames_diff = False

        if in_bnames is not None:
            if self.band_mapper.is_initialized():
                ref_bnames = self.raster.get_bname_as_list()
                is_bnames_diff = _diff_bnames(in_bnames, ref_bnames)
            else:
                is_bnames_diff = True

            if is_bnames_diff:
                return 'UPDATE_WITH_NEW_BANDS'
            else:
                return 'NO_UPDATE'

        if self.raster.initialized:
            if self.has_meta_band_map():
                meta_bnames = self.raster.get_band_names('meta')
                map_bnames = self.raster.get_band_names('map')

                if _diff_bnames(meta_bnames, map_bnames):
                    return 'COPY_FROM_META'
                else:
                    return 'NO_UPDATE'
            else:
                return 'INIT_WITH_ALL_BANDS'
        else:
            if self.has_meta_band_map():
                return 'COPY_FROM_META'
            else:
                return 'INIT_WITH_ALL_BANDS'
    
    def _execute_band_mapping_strategy(self, strategy: str, new_bnames: Optional[list[str]] = None) -> None:
        
        raw_bnames = self.raster.get_band_names('raw')

        strategies = {
            'UPDATE_WITH_NEW_BANDS': lambda: self.band_mapper.update_band_map(new_bnames),
            'COPY_FROM_META': lambda: self.band_mapper.copy_from_meta(),
            'INIT_WITH_ALL_BANDS': lambda: self.band_mapper.initialize_from_names(raw_bnames),
            'NO_UPDATE': lambda: None
        }

        if strategy not in strategies:
            raise ValueError(f'Invalid strategy: {strategy}')

        strategies[strategy]()

    
    