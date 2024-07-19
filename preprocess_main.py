import os
import argparse

from core import SCHEMA_PATH
from core.config import parse_config, load_schema_map
from core.graph import build_graph
from core.util import read_yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", default='./config/gdal.yaml', type=str)

    args = parser.parse_args()

    assert os.path.exists(args.workflow), f'workflow: {args.workflow} does not exist'

    all_config = read_yaml(args.workflow)
    schema_map = load_schema_map(SCHEMA_PATH)
    all_config, p_nodes, p_init, p_end, p_link, ops_args = parse_config(all_config, schema_map)

    g = build_graph(p_nodes, p_init, p_end, p_link, ops_args)

    wb = WorkflowBuilder(p_nodes, g)

    wb.trigger(p_init, p_nodes)
    """
    # find all paths from end to init including duplicates
    proc_paths = []
    f_g_spec = None
    for end_node in p_end:
        for start_node in p_init:
            g_spec, _ = find_all_paths(g, end_node, start_node, reverse=True, spec=f_g_spec)

    b_g_spec = None
    for start_node in p_init:
        for end_node in p_end:
            g_spec, _ = find_all_paths(g, start_node, end_node, reverse=False, spec=b_g_spec)


    # make a list of operations in each path
    all_contained_ops = make_list_of_operations_for_proc(g, proc_paths)
    dup_procs = find_path_duplicates(proc_paths)

    # check if there is a stack operation in the duplicate paths
    # todo: should be modified if any operation logic based on result split is added
    dup_rows_set = set()
    for dup_dict in dup_procs:
        dup_proc = dup_dict['dup'][-1] # last process in the duplicate path
        dup_row = dup_dict['row'][0] # first row of the duplicate paths

        try:
            dup_col = proc_paths[dup_row].index(dup_proc)
        except ValueError:
            continue

        contained_op = all_contained_ops[dup_row][dup_col]
        if 'stack' in contained_op:
            dup_rows_set.add(tuple([tuple(dup_dict['row']), dup_col]))

    print()
    # draw blueprint for implementing pre-process and execution logic
"""


if __name__ == '__main__':
    main()



