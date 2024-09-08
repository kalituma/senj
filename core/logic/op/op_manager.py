from abc import abstractmethod
from typing import TYPE_CHECKING, Type

from core.operations.parent import ChainableOp
from core.util.op import MODULE_TYPE

if TYPE_CHECKING:
    from core.operations.parent import Op
    from core.util.op import CHAIN_KEY

class OperationManager:
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
            tmp_op_name = op.name.split(':')[-1]
            if op not in op_map:
                op_map[tmp_op_name] = op
                op_count[tmp_op_name] = 1
            else:
                op_map[f'{tmp_op_name}_{op_count[tmp_op_name]}'] = op
                op_count[op.name] += 1

        return op_map

    def apply_module_type_to_ops(self, in_module_type:MODULE_TYPE):
        prev_module_type = in_module_type
        for op in self._ops:
            if op.module_type == MODULE_TYPE.NOTSET:
                op.module_type = prev_module_type
            elif op.module_type == MODULE_TYPE.CONVERT:
                prev_module_type = ~prev_module_type
            else:
                # in case of being changed by stack operation
                prev_module_type = op.module_type
        return prev_module_type

    @abstractmethod
    def set_all_op_types(self) -> MODULE_TYPE:
        pass

    @abstractmethod
    def chaining(self, prev_op:Type["Op"]=None, prev_chain_key:"CHAIN_KEY"=None):

        for op in self._ops:
            if isinstance(op, ChainableOp):
                cur_chain_key = op.chain_key

                if prev_op is None:
                    op.init_flag = True
                else:
                    if prev_chain_key == cur_chain_key:
                        op.init_flag = False
                    else:
                        op.init_flag = True
                        prev_op.end_flag = True

                prev_op = op
                prev_chain_key = cur_chain_key

            else:
                if prev_op is not None:
                    prev_op.end_flag = True

                prev_op = None
                prev_chain_key = None

        return prev_op, prev_chain_key
