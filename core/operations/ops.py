from typing import TYPE_CHECKING
from core.util.op import OP_TYPE
from core.util.errors import OPTypeNotAvailableError
from core.raster import read_band_from_raw


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
