from typing import TYPE_CHECKING
from core.util.op import OP_TYPE
from core.util.errors import OPTypeNotAvailableError
from core.raster.funcs import assert_bnames, select_band_raster


if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

class Op:
    def __init__(self, op_name):
        self._op_name:str = op_name
        self._pro_name:str = ''
        self._avail_types: list[OP_TYPE] = None
        self._op_type = None

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

    @property
    def avail_types(self):
        return self._avail_types

    @avail_types.setter
    def avail_types(self, op_types:list[OP_TYPE]):
        self._avail_types = op_types

    @property
    def op_type(self):
        return self._op_type

    @op_type.setter
    def op_type(self, op_type:OP_TYPE):
        if op_type not in self.avail_types:
            raise OPTypeNotAvailableError(self.name, op_type, self.avail_types)
        self._op_type = op_type
    def __call__(self, *args, **kwargs):
        pass

    def __str__(self):
        return ":".join([self.proc_name, self.__class__.__name__])

    def pre_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        pass

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        raster.op_history.append(self.name)
        return raster

class SelectOp(Op):
    def __init__(self, op_name, selected_bands:list[str]):
        super().__init__(op_name)
        self._selected_bands = selected_bands

    def pre_process(self, raster:"Raster", band_select:bool=False, *args, **kwargs):
        if self._selected_bands:
            assert_bnames(self._selected_bands, raster.get_band_names(), f'selected bands{self._selected_bands} should be in source bands({raster.get_band_names()})')
            if len(self._selected_bands) < len(raster.get_band_names()):
                if band_select:
                    raster = select_band_raster(raster, self._selected_bands)
        return raster

class SnapOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)
        self._snap_params = {}
    def add_param(self, **kwargs):
        self._snap_params.update(kwargs)

    def get_param(self, key:str):
        return self.snap_params[key]

    def del_param(self, key:str):
        del self.snap_params[key]

    @property
    def snap_params(self) -> dict:
        return self._snap_params

    @snap_params.setter
    def snap_params(self, snap_params:dict):
        self._snap_params = snap_params

class CachedOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def __call__(self, *args, **kwargs):
        pass

    def pre_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        pass

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        #Todo: update cached raster to raw after checking the context
        raster = super().post_process(raster, context)
        return raster
