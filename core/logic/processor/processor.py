from abc import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context
    from core.logic.executor import ProcessingExecutor
    from core.operations import Op

class Processor(metaclass=ABCMeta):

    def __init__(self, proc_name='', splittable:bool=False):
        self._proc_name:str = proc_name
        self._splittable:bool = splittable
        self.executor:"ProcessingExecutor" = None
        self.ops:list["Op"] = []

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

    def add_op(self, op:"Op"):
        op.proc_name = self.proc_name
        self.ops.append(op)
        return self

    def get_op_map(self) -> dict:
        op_map = {}
        op_count = {}

        for op in self.ops:
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
        for i, op in enumerate(self.ops):
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
        self.executor.add_ops_to_context(self.proc_name, self.get_op_map())

    def execute(self):
        if self.executor:
            return self.executor.execute(self)
        else:
            raise ValueError('Executor is not set')