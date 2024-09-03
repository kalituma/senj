from typing import TYPE_CHECKING
from dataclasses import dataclass

from core.config import parse_config
from core.graph import PINIT, PEND, PR, LINK, build_graph_func, get_procs, get_ops_args_from_graph, get_successors_by_relation

if TYPE_CHECKING:
    from networkx import DiGraph

@dataclass
class ProcessingSource:
    name:str
    ops:dict[str]
    links:list[str]

class GraphManager:
    def __init__(self, config:dict, schema_map:dict):

        # validate and parse
        n_config, procs, proc_init, proc_end, proc_link, ops_args = parse_config(config, schema_map)

        self.config:dict = n_config
        self._graph:"DiGraph" = build_graph_func(procs, proc_init, proc_end, proc_link, ops_args)
        self._procs:list[str] = get_procs(self._graph, lambda attr: attr['NODE_TYPE'] == PR)
        self._ops:list[tuple] = [get_ops_args_from_graph(self._graph, proc) for proc in self.procs]
        self._proc_op_map:dict[str] = self._build_proc_op_map()
        self.current_idx:int = 0

    @property
    def procs(self):
        return self._procs

    @property
    def ops(self):
        return self._ops

    def __len__(self):
        return len(self.procs)

    def __next__(self) -> ProcessingSource:
        if self.current_idx < len(self.procs):
            proc = self.procs[self.current_idx]
            self.current_idx += 1
            return self._get_proc_by_name(proc)
        else:
            self._reset()
            raise StopIteration

    def __iter__(self):
        return self

    def _reset(self):
        self.current_idx = 0

    def get_proc(self, idx):
        return self._get_proc_by_name(self.procs[idx])

    def _get_proc_by_name(self, proc:str) -> ProcessingSource:
        return ProcessingSource(name=proc, ops=self._proc_op_map[proc], links=self.get_next_procs(proc))

    def _build_proc_op_map(self) -> dict[str]:
        proc_op_map = {}
        for proc, p_ops in zip(self.procs, self.ops):
            proc_op_map[proc] = dict()
            proc_op_map[proc]["ops_order"] = p_ops[0]
            proc_op_map[proc]["op_args"] = {op: args for op, args in zip(p_ops[0], p_ops[1])}
        return proc_op_map

    def get_op_args(self, proc:str, op:str) -> dict:
        return self._proc_op_map[proc]['op_args'][op]

    def get_next_procs(self, proc:str) -> list[str]:
        return get_successors_by_relation(self._graph, proc, LINK)

    def is_init(self, proc:str) -> bool:
        return self._graph.nodes[proc][PINIT]

    def is_end(self, proc:str) -> bool:
        return self._graph.nodes[proc][PEND]

    def _get_proc_attr(self, proc:str):
        return self._graph.nodes[proc]