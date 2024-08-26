import unittest

from core import SCHEMA_PATH
from core.util import PathType, read_yaml
from core.config import extract_pnodes_pops, validate_in_path, remove_var_bracket, remove_func_bracket, parse_sort, replace_lambda_var_to_func, load_schema_map
from core.graph import GraphManager, ProcessorBuilder
from core.logic import Context

class TestConfigParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_path = '../resources'
        self.schema_map = load_schema_map(SCHEMA_PATH)

        self.stack_config_path = f'{self.resource_path}/config/stack.yaml'
        self.stack_config = read_yaml(self.stack_config_path)

    def test_graph_manager_item(self):
        with self.subTest(msg='stack.yaml'):
            stack_config_path = f'{self.resource_path}/config/stack.yaml'
            stack_config = read_yaml(stack_config_path)

            graph_manager = GraphManager(stack_config, self.schema_map)
            self.assertEqual(graph_manager.get_proc(0).ops['ops_order'], ['input', 'read'])
            self.assertEqual(graph_manager.get_proc(0).links, ['stack_s2_1_2'])

        with self.subTest(msg='s1'):
            s1_config_path = f'{self.resource_path}/config/s1_write.yaml'
            s1_config = read_yaml(s1_config_path)

            graph_manager = GraphManager(s1_config, self.schema_map)
            self.assertEqual(graph_manager.get_proc(0).ops['ops_order'], ['input', 'read', 'apply_orbit', 'calibrate', 'terrain_correction'])
            self.assertEqual(graph_manager.get_proc(0).links, [])

    def test_processor_builder_stack(self):
        graph_manager = GraphManager(self.stack_config, self.schema_map)
        with Context(graph_manager) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()

        self.assertEqual(len(end_points), 1)
