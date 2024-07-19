import networkx

from core.graph import PINIT, PEND, OINIT, OEND, PR, OP, IP, INCLUDE, LINK, GEN

def build_graph(p_nodes:list[str], p_init:list[str], p_end:list[str], p_link, ops_args:dict) -> networkx.DiGraph:

    graph = networkx.DiGraph()

    # add process nodes and operations with op links
    for p_node in p_nodes:
        if p_node in p_init:
            graph.add_node(p_node, node_type=PR, process_type=PINIT)
        if p_node in p_end:
            graph.add_node(p_node, node_type=PR, process_type=PEND)

        prev_op_name = None
        for i, op_value in enumerate(ops_args[p_node]):

            op_name = ":".join([p_node, op_value['op_name']])
            if op_value['op_name'] == 'input':
                graph.add_node(op_name, node_type=IP, args=op_value['args'])
                graph.add_edge(p_node, op_name, relation=GEN)
            else:
                graph.add_node(op_name, node_type=OP, args=op_value['args'])
                graph.add_edge(p_node, op_name, relation=INCLUDE, order=i)

            if i > 0:
                graph.add_edge(prev_op_name, op_name, relation=LINK)
            prev_op_name = op_name

    # add process links
    for link in p_link:
        graph.add_edge(link[0], link[1], relation=LINK)

    return graph


