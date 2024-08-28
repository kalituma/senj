from abc import abstractmethod
from typing import TYPE_CHECKING, Type

from core.util.op import OP_TYPE

if TYPE_CHECKING:
    from core.operations.parent import Op



class OperationManager():
    def __init__(self):
        self._ops: list[Type["Op"]] = []

    @property
    def ops(self):
        return self._ops

    @ops.setter
    def ops(self, ops: list[Type["Op"]]):
        self._ops = ops

    def add_op(self, op: Type["Op"]):
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

    @abstractmethod
    def apply_op_type_from_root_proc(self) -> OP_TYPE:
        pass

    def apply_op_type(self, in_op_type:OP_TYPE):
        prev_op_type = in_op_type
        for op in self._ops:
            if op.op_type == OP_TYPE.NOTSET:
                op.op_type = prev_op_type
            elif op.op_type == OP_TYPE.CONVERT:
                prev_op_type = not prev_op_type
            else:
                # in case of being changed by stack operation
                prev_op_type = op.op_type
        return prev_op_type