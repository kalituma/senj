from abc import *
from typing import TYPE_CHECKING, Type
from enum import Enum

from core.util.op import OP_TYPE

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context
    from core.logic.executor import ProcessingExecutor
    from core.operations import Op

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


class Processor(metaclass=ABCMeta):

    def __init__(self, proc_name='', proc_type:ProcessorType=None, splittable:bool=False):

        self._proc_name:str = proc_name
        self._proc_type: ProcessorType = proc_type
        self._splittable:bool = splittable
        self.executor:"ProcessingExecutor" = None
        self._ops:list[Type["Op"]] = []

    @property
    def splittable(self):
        return self._splittable

    @splittable.setter
    def splittable(self, splittable:bool):
        self._splittable = splittable

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
    def ops(self):
        return self._ops

    @ops.setter
    def ops(self, ops:list[Type["Op"]]):
        self._ops = ops

    def add_op(self, op:Type["Op"]):
        op.proc_name = self.proc_name
        self._ops.append(op)
        return self

    def get_op_map(self) -> dict:
        op_map = {}
        op_count = {}

        for op in self._ops:
            tmp_op_name = op.name.split('_')[-1]
            if op not in op_map:
                op_map[tmp_op_name] = op
                op_count[tmp_op_name] = 1
            else:
                op_map[f'{tmp_op_name}_{op_count[tmp_op_name]}'] = op
                op_count[op.name] += 1

        return op_map

    def process(self, input:"Raster", ctx:"Context"):
        x = input
        for i, op in enumerate(self._ops):
            x = op(x, ctx)
        return x

    @abstractmethod
    def preprocess(self, *args, **kwargs):
        pass

    @abstractmethod
    def postprocess(self, x):
        pass

    def set_executor(self, executor:"ProcessingExecutor"):
        self.executor = executor

    @abstractmethod
    def get_prev_last_op_type(self) -> OP_TYPE:
        pass

    def set_op_type(self, prev_proc_op_type:OP_TYPE):
        prev_op_type = prev_proc_op_type
        for op in self._ops:
            if op.op_type == OP_TYPE.NOTSET:
                op.op_type = prev_op_type
            elif op.op_type == OP_TYPE.CONVERT:
                prev_op_type = not prev_op_type
            else:
                continue
        return prev_op_type

    def execute(self):
        if self.executor:
            return self.executor.execute(self)
        else:
            raise ValueError('Executor is not set')

