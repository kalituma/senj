from typing import TYPE_CHECKING, Type, List

from core.util.logger import Logger, print_log_attrs
from core import PROCESSOR, OPERATIONS
from core.logic import FILE_PROCESSOR, LINK_PROCESSOR, Context, ContextManager
from core.logic.executor import ProcessingExecutor
from core.logic.processor import ProcessorType

if TYPE_CHECKING:
    from core.logic.processor import Processor

class ProcessorBuilder(ContextManager):
    def __init__(self, context:Context):
        super().__init__(context)
        self._logger = Logger.get_logger()
        self._processor_map:dict[str, Type["Processor"]] = {}
        self._end_points:List[Type["Processor"]] = []
        self._executor:"ProcessingExecutor" = ProcessingExecutor(context)

    @property
    def end_point(self) -> list[Type["Processor"]]:
        return self._end_points

    def build_op_args(self, op, op_args):
        return op_args

    def build_operations(self, proc_name:str, ops:dict[str]):

        assert proc_name in self._processor_map, f'{proc_name} obj should be built before building operations.'

        for op in ops['ops_order']:
            if op != 'input':
                op_args = self.build_op_args(op, ops['op_args'][op])
                constructor = OPERATIONS.__get_attr__(name=op, attr_name='constructor')

                built_op_instance = constructor(**op_args)
                self._processor_map[proc_name].add_op(op=built_op_instance)

        return self._processor_map[proc_name].ops

    def build_processor(self, proc_name:str):
        if proc_name in self._processor_map:
            return self._processor_map[proc_name]

        if self._graph_manager.is_init(proc_name):
            constructor = PROCESSOR.__get_attr__(FILE_PROCESSOR, 'constructor')
            input_args = self._context._graph_manager.get_op_args(proc_name, 'input')
        else:
            constructor = PROCESSOR.__get_attr__(LINK_PROCESSOR, 'constructor')
            input_args = {}

        self._processor_map[proc_name] = constructor(proc_name=proc_name, **input_args)

        if self._graph_manager.is_end(proc_name):
            self._end_points.append(self._processor_map[proc_name])

        return self._processor_map[proc_name]

    def connect_link(self):
        for graph_elem in self._context._graph_manager:
            for after_proc in graph_elem.links:
                if self._processor_map[after_proc].proc_type == ProcessorType.LINK:
                    self._processor_map[after_proc].add_linked_process(self._processor_map[graph_elem.name])
                else:
                    raise ValueError(f'Processor {after_proc} should be of type LINK_PROCESSOR')

    def build_executor(self):
        for end_point in self._end_points:
            end_point.set_all_op_types()
            end_point.chaining()
            end_point.set_executor(self._executor)

    def build(self) -> list[Type["Processor"]]:
        self._logger.log('info', '------------------------------------------------------ start to build processor')
        tmp_proc_list = []
        for graph_elem in self._context._graph_manager:
            tmp_proc_list.append(self.build_processor(proc_name=graph_elem.name))
            self.build_operations(proc_name=graph_elem.name, ops=graph_elem.ops) # check available op types
            # print_log_attrs(tmp_processor, 'debug')

        self.connect_link() # set op type based on read module

        for proc in tmp_proc_list:
            print_log_attrs(proc, 'debug')

        self.build_executor()
        self._logger.log('info', '------------------------------------------------------ finished building processor')

        return self.end_point
