from typing import TYPE_CHECKING
from core.raster import read_band_from_raw

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

class Op:
    def __init__(self, op_name):
        self._op_name = op_name
        self._pro_name = '' 

    @property
    def name(self):
        return '_'.join([self.proc_name, self.op_name])

    @property
    def proc_name(self):
        return self._pro_name

    @proc_name.setter
    def proc_name(self, value):
        self._pro_name = value

    @property
    def op_name(self):
        return self._op_name

    def __call__(self, *args, **kwargs):
        pass

    def __str__(self):
        return ":".join([self.proc_name, self.__class__.__name__])

    def pre_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        pass

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        raster.op_history.append(self.name)
        return raster

class CachedOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def __call__(self, *args, **kwargs):
        pass

    def pre_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        if not raster.is_band_cached:
            selected_bands = raster.selected_bands if raster.selected_bands else None
            raster = read_band_from_raw(raster, selected_bands)
        return raster

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        #Todo: update cached raster to raw after checking the context
        raster = super().post_process(raster, context)
        return raster
