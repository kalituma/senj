from networkx import DiGraph
from typing import TYPE_CHECKING
from core.graph import PINIT, PEND, PBRIDGE, PR, OP, INCLUDE, LINK

if TYPE_CHECKING:
    from core.util import PathType

def build_graph_func(p_nodes:list[str], p_init:dict[str, "PathType"], p_end:list[str], p_link:list[tuple], ops_args:dict) -> DiGraph:

    graph = DiGraph()

    # add process nodes and operations with op links
    for p_node in p_nodes:
        graph.add_node(p_node, NODE_TYPE=PR, PINIT=False, PEND=False, PBRIDGE=False)

        if p_node in p_init:
            graph.nodes[p_node][PINIT] = True
        if p_node in p_end:
            graph.nodes[p_node][PEND] = True

        if not graph.nodes[p_node][PINIT] and not graph.nodes[p_node][PEND]:
            graph.nodes[p_node][PBRIDGE] = True

        prev_op_name = None
        for i, op_value in enumerate(ops_args[p_node]):
            op_name = ":".join([p_node, op_value['op_name']])
            graph.add_node(op_name, NODE_TYPE=OP, ARGS=op_value['args'])
            graph.add_edge(p_node, op_name, INDEX=i, RELATION=INCLUDE)

            if i > 0:
                graph.add_edge(prev_op_name, op_name, RELATION=LINK)

            prev_op_name = op_name

    # add process and operation links
    for before_node, after_node in p_link:
        graph.add_edge(before_node, after_node, RELATION=LINK)
        before_op_map = { attr['INDEX']:neighbor for neighbor, attr in graph.adj[before_node].items() if attr['RELATION'] == INCLUDE}
        after_op_map = { attr['INDEX']:neighbor for neighbor, attr in graph.adj[after_node].items() if attr['RELATION'] == INCLUDE}
        before_last_key = list(before_op_map.keys())[-1]
        after_first_key = list(before_op_map.keys())[0]

        graph.add_edge(before_op_map[before_last_key], after_op_map[after_first_key], RELATION=LINK)

    return graph