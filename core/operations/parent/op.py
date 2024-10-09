from typing import TYPE_CHECKING, Type, List, Union, AnyStr
from core.raster import Raster
from core.logic.event import EventEmitter
from core.util.op import OP_Module_Type
from core.util.errors import OPTypeNotAvailableError
from core.util.logger import Logger, print_log_attrs

if TYPE_CHECKING:
    from core.logic import Context

class LogCall(type):
    def __new__(mcs, name, bases, attrs):
        if '__call__' in attrs:
            original_call = attrs['__call__']

            def wrapped_call(self, *args, **kwargs):
                self.start_log()
                print_log_attrs(self, 'debug')
                try:
                    result = original_call(self, *args, **kwargs)
                    return result
                finally:
                    self.end_log(result)

            attrs['__call__'] = wrapped_call
        return super().__new__(mcs, name, bases, attrs)

class Op(EventEmitter, metaclass=LogCall):
    def __init__(self, op_name):
        super().__init__()

        self._op_name:str = op_name
        self._pro_name:str = ''
        self._avail_types: list[OP_Module_Type] = None
        self._must_after: Type[Op] = None
        self._module_type:OP_Module_Type = OP_Module_Type.from_str(op_name) if op_name in ['convert'] else OP_Module_Type.NOTSET
        self._counter = 0
        self._logger = Logger.get_logger()

    @property
    def name(self):
        return ':'.join([self.proc_name, self.op_name])

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
    def avail_types(self, op_types:list[OP_Module_Type]):
        self._avail_types = op_types

    @property
    def module_type(self):
        return self._module_type

    @module_type.setter
    def module_type(self, op_type:Union[OP_Module_Type, AnyStr]):

        if isinstance(op_type, str):
            op_type = OP_Module_Type.from_str(op_type)

        if op_type not in self.avail_types:
            raise OPTypeNotAvailableError(self.name, op_type, self.avail_types)
        self._module_type = op_type
        self.emit('op_type_changed', op_type)

    @property
    def must_after(self):
        return self._must_after

    @must_after.setter
    def must_after(self, must_after:Type["Op"]):
        self._must_after = must_after

    @property
    def counter(self):
        return self._counter

    def reset_counter(self):
        self._counter = 0

    def __increase_counter(self):
        self._counter += 1

    def __str__(self):
        return ":".join([self.proc_name, self.__class__.__name__])

    def pre_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        pass

    def post_process(self, raster:"Raster", context:"Context", *args, **kwargs):
        raster.op_history.append(self.name)
        self.__increase_counter()
        return raster

    def log(self, msg, level='info'):
        self._logger.log(level, f'({self.__class__.__name__}) {msg}')

    def start_log(self):
        self.log(f'------------------------------------------------------ call {self.__class__.__name__}')

    def end_log(self, result:Union['Raster', str]):
        if isinstance(result, Raster):
            self.log(f'bands_to_index : {result.band_to_index}')
            self.log(f'------------------------------------------------------ history: {result.op_history}')
        self.log(f'------------------------------------------------------ end {self.__class__.__name__} (counter:{self.counter})')









