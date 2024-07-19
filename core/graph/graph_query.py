from core.graph import PINIT, PEND, PR, OP, LINK, INCLUDE

def get_parent_processors(graph, proc_name):
    return get_predecessors_by_relation(graph, proc_name, LINK)

def get_child_processors(graph, proc_name):
    return get_successors_by_relation(graph, proc_name, LINK)

def get_predecessors_by_relation(graph, node, relation):
    return [predecessor for predecessor in graph.predecessors(node) if graph.get_edge_data(predecessor, node).get('relation') == relation]

def get_successors_by_relation(graph, node, relation):
    return [successor for successor in graph.successors(node) if graph.get_edge_data(node, successor).get('relation') == relation]

def get_end_procs(graph):
    return [node for node, attrs in graph.nodes(data=True) if attrs.get('node_type') == PR and attrs.get('process_type') == PEND]

def make_list_of_operations_for_proc(graph, proc_nodes_list:list):

    op_list = []
    for proc_nodes in proc_nodes_list:
        proc_op_nodes = []
        for proc_node in proc_nodes:
            op_nodes, _ = get_ops_using_proc(graph, proc_node)
            proc_op_nodes.append(op_nodes)
        op_list.append(proc_op_nodes)

    return op_list

def get_ops_using_proc(graph, proc_node, q_relation=INCLUDE):
    op_nodes = []
    op_atts = []
    for successor in graph.successors(proc_node):
        edge_data = graph.get_edge_data(proc_node, successor)
        if edge_data.get('relation') == q_relation:
            op_name = successor[len(proc_node) + 1:]
            op_nodes.append(op_name)
            op_atts.append(graph.nodes[successor]['args'])
    return op_nodes, op_atts


def find_all_paths(graph, start, end, reverse=False, path=None, spec=None):

    if path is None:
        path = []

    if spec is None:
        spec = dict()

    path = path + [start]

    if start not in spec:
        spec[start] = {}

    if 'op' not in spec[start]:
        spec[start]['op'], _ = get_ops_using_proc(graph, start)
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