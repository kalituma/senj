from typing import Callable

from networkx import DiGraph
from core.graph import PINIT, PEND, PR, OP, LINK, INCLUDE

def get_parent_processors(graph, proc_name):
    return get_predecessors_by_relation(graph, proc_name, LINK)

def get_child_processors(graph, proc_name):
    return get_successors_by_relation(graph, proc_name, LINK)

def get_procs(graph:DiGraph, lambda_func:Callable[..., bool]):
    return [node for node, attr in graph.nodes(data=True) if lambda_func(attr)]

def get_predecessors_by_relation(graph, node, relation):
    return [predecessor for predecessor in graph.predecessors(node) if graph.get_edge_data(predecessor, node).get('RELATION') == relation]

def get_successors_by_relation(graph, node, relation):
    return [successor for successor in graph.successors(node) if graph.get_edge_data(node, successor).get('RELATION') == relation]

def get_ops_args(graph:DiGraph, proc:str, q_relation:str=INCLUDE) -> tuple[list, list]:
    ops = []
    args = []

    for successor in graph.successors(proc):
        edge_attr = graph.get_edge_data(proc, successor)
        if edge_attr.get('RELATION') == q_relation:
            op_name = successor.split(':')[1]
            op_args = graph.nodes[successor]['ARGS']
            ops.append(op_name)
            args.append(op_args)

    return ops, args

def find_all_paths(graph, start, end, reverse=False, path=None, spec=None):

    if path is None:
        path = []

    if spec is None:
        spec = dict()

    path = path + [start]

    if start not in spec:
        spec[start] = {}

    if 'op' not in spec[start]:
        spec[start]['op'], _ = get_ops_from_proc(graph, start)
        spec[start]['link'] = []

    #last step
    if start == end:
        # if start node touched end node, return the end node
        return spec, [path]
    if start not in graph:
        # reached wrong end node
        return None, []
    paths = []

    if reverse:
        succs = get_predecessors_by_relation(graph, start, LINK)
    else:
        succs = get_successors_by_relation(graph, start, LINK)

    for node in succs:
        if node not in path:
            if node not in spec[start]['link']:
                spec[start]['link'].append(node)
            spec, new_paths = find_all_paths(graph, node, end, reverse, path, spec)
            for new_path in new_paths:
                paths.append(new_path)
    return spec, paths

def query_network_reverse(graph, end_node):
    visited = set()
    stack = [end_node]
    paths = []

    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            path = [node]
            current = node

        while True:
            predecessors = get_predecessors_by_relation(graph, current, LINK)
            if not predecessors:
                break
            prev = predecessors[0]
            path.append(prev)
            current = prev

        paths.append(path)
        stack.extend(set(get_successors_by_relation(graph, node, LINK)) - visited)

    return paths

def find_path_duplicates(paths):
    result = []
    max_length = max(len(path) for path in paths)

    for length in range(1, max_length + 1):
        dup_dict = {}
        for i, path in enumerate(paths):
            if len(path) >= length:
                key = tuple(path[:length])
                if key not in dup_dict:
                    dup_dict[key] = []
                dup_dict[key].append(i)

        for key, rows in dup_dict.items():
            if len(rows) > 1:
                result.append({
                    'dup': list(key),
                    'row': rows
                })
    return result