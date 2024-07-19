from copy import deepcopy

from core.logic import FILE_PROCESSOR, LINK_PROCESSOR
from core.graph import GEN
from core.graph import build_graph, get_ops_using_proc, get_child_processors, get_parent_processors

class WorkflowBuilder:
    def __init__(self, proc_nodes, proc_init, proc_end, proc_link, ops_args):
        self._graph = build_graph(proc_nodes, proc_init, proc_end, proc_link, ops_args)

    def trigger(self, init_processes:list, all_processes:list):

        build_map = dict()
        visited = set()

        for c_proc in init_processes:
            build_map, visited = self.trigger_recur(c_proc, build_map, visited)

    def trigger_recur(self, proc_name, build_map, visited:set, prev_proc=None):

        f_nodes = get_child_processors(self._graph, proc_name)

        if proc_name in visited:
            for f_i, f_node in enumerate(f_nodes):
                b_nodes = get_parent_processors(self._graph, proc_name)
                for b_i, b_node in enumerate(b_nodes):
                    if b_node != prev_proc.proc_name:
                        exist_key = f'{b_node}->{proc_name}:f{f_i}'
                        key = f'{prev_proc.proc_name}->{proc_name}:f{f_i}'
                        if exist_key in build_map:
                            build_map[key] = build_map[exist_key]
                            build_map[key].add_linked_process(prev_proc)
                            break
            return build_map, visited

        c_proc_type = self._check_process_type(proc_name, self._graph)

        ops, ops_atts = get_ops_using_proc(self._graph, proc_name)

        processor = None
        for f_i, f_node in enumerate(f_nodes):
            if f_i == 0:
                processor = self.visit_node(ops, ops_atts, c_proc_type, proc_name, prev_proc)
            else:
                processor = deepcopy(processor)

            prev_name = '' if prev_proc is None else prev_proc.proc_name
            build_key = f'{prev_name}->{proc_name}:f{f_i}'
            build_map[build_key] = processor
            b_nodes = get_parent_processors(self._graph, f_node)

            build_map, visited = self.trigger_recur(f_node, build_map, visited, processor)

        if len(f_nodes) == 0:
            processor = self.visit_node(ops, ops_atts, c_proc_type, proc_name, prev_proc)
            prev_name = '' if prev_proc is None else prev_proc.proc_name
            build_map[f'{prev_name}->{proc_name}:0'] = processor

        visited.add(proc_name)

        return build_map, visited

    def visit_node(self, ops, ops_atts, c_proc_type, proc_name, prev_proc):
        processor_builder = ProcessorBuilder().add_operations(ops, ops_atts)
        if c_proc_type == FILE_PROCESSOR:
            inp, inp_atts = get_ops_using_proc(self._graph, proc_name, q_relation=GEN)
            processor = processor_builder.make_processor(c_proc_type, proc_name, **inp_atts[0]).build()
        else:
            processor_builder.make_processor(c_proc_type, proc_name)
            assert prev_proc is not None, f'You cannot make a link processor when prev_proc is not None'
            processor = processor_builder.add_linked_process(prev_proc).build()
        return processor

    def _check_process_type(self, proc_name, graph):
        ops, _ = get_ops_using_proc(graph, proc_name)
        if 'read' in ops:
            return FILE_PROCESSOR
        else:
            return LINK_PROCESSOR

    def build(self):
        return self._workflow