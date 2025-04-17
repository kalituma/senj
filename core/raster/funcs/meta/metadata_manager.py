from typing import Optional
from core.raster import RasterMeta
from core.raster.funcs.meta import BandMapper, BandMapEvent

class MetaDictManager:
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
        return self.raster.has_meta_dict
    
    def has_meta_band_map(self):
        return self.raster.has_meta_band_map
    
    def _setup_event_listners(self):
        self.band_mapper.add_observer(BandMapEvent.INITIALIZED, self.band_mapper.copy_to_meta)
        self.band_mapper.add_observer(BandMapEvent.UPDATED, self.band_mapper.copy_to_meta)    
    
    def update_band_mapping(self, bnames: Optional[list[str]] = None) -> None:
        strategy = self._determine_band_mapping_strategy(bnames)
        self._execute_band_mapping_strategy(strategy, bnames)  

    def _determine_band_mapping_strategy(self, bnames: Optional[list[str]] = None) -> str:
        
        is_bnames_diff = False

        if bnames is not None:
            if self.band_mapper.is_initialized:
                ref_bnames = self.raster.get_bname_as_list()            
                if set(bnames) == set(ref_bnames):
                    is_bnames_diff = False
                else:
                    is_bnames_diff = True
            else:
                is_bnames_diff = True

        if is_bnames_diff:
            return 'UPDATE_WITH_NEW_BANDS'
        else:
            if self.band_mapper.is_initialized:
                if self.has_meta_band_map:
                    return 'COPY_FROM_META'
            else:
                if self.has_meta_dict:
                    if self.has_meta_band_map:
                        return 'COPY_FROM_META'
                    else:
                        return 'INIT_WITH_ALL_BANDS'
                else:
                    return 'INIT_WITH_ALL_BANDS'                
        
        raise ValueError('Cannot find strategy for band mapping')
    
    def _execute_band_mapping_strategy(self, strategy: str, bnames: Optional[list[str]] = None) -> None:
        
        all_bnames = self.raster.get_band_names()

        strategies = {
            'UPDATE_WITH_NEW_BANDS': lambda: self.band_mapper.update_band_map(bnames),
            'COPY_FROM_META': lambda: self.band_mapper.copy_from_meta(),
            'INIT_WITH_ALL_BANDS': lambda: self.band_mapper.initialize_from_names(all_bnames),
        }

        if strategy not in strategies:
            raise ValueError(f'Invalid strategy: {strategy}')

        strategies[strategy]()

    
    