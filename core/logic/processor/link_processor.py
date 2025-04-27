from typing import TYPE_CHECKING, Type, Union, AnyStr

from core import PROCESSOR
from core.util.op import OP_Module_Type
from core.logic import LINK_PROCESSOR
from core.logic.processor import Processor, ProcessorType
from core.raster import Raster

if TYPE_CHECKING:
    from core.logic.executor import ProcessingExecutor
    from core.util.op import CHAIN_KEY

@PROCESSOR.reg(LINK_PROCESSOR)
class LinkProcessor(Processor):
    def __init__(self, proc_name:str='', processors:list[Type[Processor]]=None, splittable:bool=False):
        super().__init__(proc_name=proc_name, proc_type=ProcessorType.LINK, splittable=splittable)
        if processors is None:
            self.proc_list = []
        else:
            self.proc_list = processors

    def __contains__(self, proc):
        return proc in self.proc_list

    def add_linked_process(self, linked_proc:Type[Processor]):
        self.proc_list.append(linked_proc)
        return self

    def preprocess(self):

        if len(self.proc_list) == 1:
            gens = self.proc_list[0].execute()
        else:
            gens = [single_executor.execute() for single_executor in self.proc_list]

        def safe_next(gen):
            try:
                return next(gen), False
            except StopIteration:
                return None, True

        while True:
            try:
                if len(self.proc_list) == 1:
                    yield next(gens)
                else:
                    results = []
                    any_stopped = False
                    for proc_gen in gens:
                        result, stopped = safe_next(proc_gen)
                        any_stopped = any_stopped or stopped
                        results.append(result)

                    if any_stopped:
                        break

                    yield results
            except StopIteration as e:
                break

    def postprocess(self, x:Union[Raster, AnyStr], result_clone:bool=False):
        if isinstance(x, Raster):
            x = super().postprocess(x)
        return x

    def set_executor(self, executor:"ProcessingExecutor"):

        super().set_executor(executor)

        for single_process in self.proc_list:
            if isinstance(single_process, Processor):
                single_process.set_executor(executor)

    def get_first_op_type(self) -> OP_Module_Type:
        if self.ops[0].module_type == OP_Module_Type.NOTSET:
            raise ValueError('First operation type is not set yet.')
        return self.ops[0].module_type

    def set_all_op_types(self) -> OP_Module_Type:
        prev_op_types = []
        for proc in self.proc_list:
            prev_op_types.append(proc.set_all_op_types())

        if len(set(prev_op_types)) == 1:
            return self.apply_module_type_to_ops(prev_op_types[0])
        else:
            # multiple type of op is meaning the only case the first op is stack operation already set with specific module type
            return self.apply_module_type_to_ops(self.get_first_op_type())

    def chaining(self):
        proc_prev_ops = []
        proc_prev_chain_keys = []

        for proc in self.proc_list:
            prev_op, prev_chain_key = proc.chaining()
            proc_prev_chain_keys.append(prev_chain_key)
            proc_prev_ops.append(prev_op)

        out_op, out_chain_key = None, None
        for prev_op, prev_chain_key in zip(proc_prev_ops, proc_prev_chain_keys):
            out_op, out_chain_key = super().chaining(prev_op, prev_chain_key)

        return out_op, out_chain_key