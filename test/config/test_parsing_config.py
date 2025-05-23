import unittest
from functools import partial

from core import SCHEMA_PATH
from core.util import PathType, read_yaml
from core.lambda_funcs import sort_by_name
from core.config import extract_pnodes_pops, validate_input_path, remove_var_bracket, remove_func_bracket, parse_sort, replace_config_properties_after, load_schema_map, parse_config
from core.graph import build_graph_func

class TestConfigParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_path = '../resources'

        self.read_config_path = f'{self.resource_path}/config/stack_read.yaml'
        self.read_config = read_yaml(self.read_config_path)

        self.schema_map = load_schema_map(SCHEMA_PATH)

        self.stack_config_path = f'{self.resource_path}/config/stack.yaml'
        self.stack_config = read_yaml(self.stack_config_path)
    def delete_not_dict(self):
        result = dict()
        for key, value in self.read_config.items():
            if isinstance(value, dict):
                result[key] = value
        return result

    def test_extract_pnodes(self):
        p_nodes, p_ops, n_config = extract_pnodes_pops(self.read_config)
        self.assertEqual(p_nodes, list(n_config.keys()))

        ops_target = {key: [] for key in n_config.keys()}
        self.assertEqual(p_ops, ops_target)

    def test_validate_in_path(self):
        input_checks = validate_input_path(self.read_config['read_s2_1']['input']['path'])
        self.assertEqual(input_checks, [(True, PathType.DIR)])

    def test_validate_in_path_2(self):
        input_checks = validate_input_path(self.read_config['read_s2_2']['input']['path'])
        self.assertEqual(input_checks, [(True, PathType.DIR), (True, PathType.DIR)])

    def test_validate_in_path_3(self):
        input_checks = validate_input_path(self.read_config['read_s2_3']['input']['path'])
        self.assertEqual(input_checks, [(False, PathType.VAR), (False, PathType.VAR)])

    def test_validate_in_path_4(self):
        input_checks = validate_input_path(self.read_config['read_s2_4']['input']['path'])
        self.assertEqual(input_checks, [(False, PathType.VAR)])

    def test_remove_var_bracket(self):
        self.assertEqual(remove_var_bracket('{{test}}'), 'test')

    def test_parse_sort(self):
        from functools import partial
        sort_atts = self.read_config['read_s2_1']['input']
        self.assertEqual(isinstance(parse_sort(sort_atts)['sort']['func'], partial), True)

    def test_remove_func_bracket(self):
        self.assertEqual(remove_func_bracket('!{test}'), 'test')

    def test_lambda_var_to_func(self):
        new_config = replace_config_properties_after(self.read_config['read_s2_4'].copy())
        self.assertEqual(new_config['input']['sort']['func'], sort_by_name)

    def test_parse_config(self):

        all_config, p_nodes, p_init, p_end, p_link, ops_args = parse_config(self.stack_config, self.schema_map)

        self.assertEqual(isinstance(all_config['read_s2_1']['input']['sort']['func'], partial), True)
        self.assertEqual(p_nodes, ['read_s2_1', 'read_s2_2', 'stack_s2_1_2'])
        self.assertEqual(p_init, {'read_s2_1': PathType.DIR, 'read_s2_2': PathType.DIR})
        self.assertEqual(p_end, ['stack_s2_1_2'])
        self.assertEqual(p_link, [('read_s2_1', 'stack_s2_1_2'), ('read_s2_2', 'stack_s2_1_2')])
        self.assertEqual(ops_args['read_s2_1'], [{'op_name': 'input', 'args': all_config['read_s2_1']['input']}, {'op_name': 'read', 'args': all_config['read_s2_1']['read']}])

    def test_build_graph(self):
        all_config, p_nodes, p_init, p_end, p_link, ops_args = parse_config(self.stack_config, self.schema_map)
        graph = build_graph_func(p_nodes, p_init, p_end, p_link, ops_args)

