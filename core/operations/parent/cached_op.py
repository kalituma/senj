from typing import TYPE_CHECKING, List, AnyStr
from core.operations.parent import Op
from core.raster.funcs import read_band_from_raw, update_raw_from_cache

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

class CachedOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def __call__(self, *args, **kwargs):
        pass

    def pre_process(self, data: "Raster", context: "Context", *args, **kwargs):

        bands_to_load = kwargs['bands_to_load']
        target_raster = read_band_from_raw(data, bands_to_load, add_to_cache=True)
        self._logger.log('DEBUG', f'({self.__class__.__name__})-->preprocess : {bands_to_load} bands are loaded from raw')
        return target_raster

    def post_process(self, raster:"Raster", context:"Context", clear=False, *args, **kwargs):
        raster = update_raw_from_cache(raster, clear=clear)
        raster = super().post_process(raster, context)
        self._logger.log('DEBUG', f'({self.__class__.__name__})-->postprocess : bands({raster.get_cached_band_names()}) are updated to raw')
        return raster