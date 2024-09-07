from abc import abstractmethod
from typing import TYPE_CHECKING, AnyStr, Union
from enum import Enum


from core.logic.op import OperationManager

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context
    from core.logic.executor import ProcessingExecutor

class ProcessorType(Enum):
    FILE = 'FileProcessor'
    LINK = 'LinkProcessor'

    def __str__(self):
        return self.value

    def from_str(self, s:str):
        if s == 'FileProcessor':
            return ProcessorType.FILE
        elif s == 'LinkProcessor':
            return ProcessorType.LINK
        else:
            raise ValueError(f'Unknown ProcessorType: {s}')


class Processor(OperationManager):

    def __init__(self, proc_name='', proc_type:ProcessorType=None, splittable:bool=False):

        super().__init__()
        self._proc_name:str=proc_name
        self._proc_type: ProcessorType = proc_type
        self._splittable:bool = splittable
        self.executor:"ProcessingExecutor" = None


    @property
    def proc_name(self):
        return self._proc_name

    @proc_name.setter
    def proc_name(self, proc_name:str):
        self._proc_name = proc_name

    @property
    def proc_type(self):
        return self._proc_type

    @proc_type.setter
    def proc_type(self, proc_type:ProcessorType):
        self._proc_type = proc_type

    @property
    def splittable(self):
        return self._splittable

    @splittable.setter
    def splittable(self, splittable:bool):
        self._splittable = splittable

    def process(self, input:"Raster", ctx:"Context"):
        x = input
        for i, op in enumerate(self._ops):
            x = op(x, ctx)
        return x

    @abstractmethod
    def preprocess(self, *args, **kwargs):
        pass

    @abstractmethod
    def postprocess(self, x:"Raster"):
        x.raster_from = self.proc_name
        return x

    def set_executor(self, executor:"ProcessingExecutor"):
        self.executor = executor

    def execute(self):
        if self.executor:
            return self.executor.execute(self)
        else:
            raise ValueError('Executor is not set')



