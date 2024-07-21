from typing import TYPE_CHECKING
from core import PROCESSOR, OPERATIONS
from core.logic import FILE_PROCESSOR, LINK_PROCESSOR, Context
from core.logic.executor import ProcessingExecutor

if TYPE_CHECKING:
    from core.graph import GraphManager, ProcessingSource
    from core.logic import Processor

class ProcessorBuilder:
    def __init__(self, graph_manager:"GraphManager"):
        self._graph_manager = graph_manager
        self._processor_map = {}
        self._end_point:list["Processor"] = []

    @property
    def end_point(self) -> list["Processor"]:
        return self._end_point

    def build_op_args(self, op, op_args):
        if op == 'write':
            op_args['out_ext'] = op_args['ext']
            del op_args['ext']
        return op_args

    def build_operation(self, graph_elem: "ProcessingSource"):

        proc = graph_elem.name
        assert proc in self._processor_map, f'{proc} obj should be built before building operations.'
        ops = graph_elem.ops

        for op in ops['ops_order']:
            if op != 'input':
                op_args = self.build_op_args(op, ops['op_args'][op])
                constructor = OPERATIONS[op]
                self._processor_map[proc].add_op(constructor(**op_args))

    def build_processor(self, graph_elem: "ProcessingSource"):
        proc = graph_elem.name
        if proc in self._processor_map:
            return self._processor_map[proc]

        if self._graph_manager.is_init(proc):
            constructor = PROCESSOR[FILE_PROCESSOR]
            input_args = self._graph_manager.get_op_args(proc, 'input')
        else:
            constructor = PROCESSOR[LINK_PROCESSOR]
            input_args = {}

        self._processor_map[proc] = constructor(proc_name=proc, **input_args)
        self.build_operation(graph_elem)

        if self._graph_manager.is_end(proc):
            self._end_point.append(self._processor_map[proc])

        return self._processor_map[proc]

    def connect_link(self):
        for graph_elem in self._graph_manager:
            for next_proc in graph_elem.links:
                self._processor_map[next_proc].add_linked_process(self._processor_map[graph_elem.name])

    def build_executor(self):
        self._executors = ProcessingExecutor(Context())
        for end_point in self._end_point:
            end_point.set_executor(self._executors)

    def build(self) -> list["Processor"]:
        for graph_elem in self._graph_manager:
            self.build_processor(graph_elem)
        self.connect_link()
        self.build_executor()

        return self.end_point