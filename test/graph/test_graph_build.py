import unittest

from core import SCHEMA_PATH
from core.util import PathType, read_yaml
from core.config import extract_pnodes_pops, validate_in_path, remove_var_bracket, remove_func_bracket, parse_sort, replace_lambda_var_to_func, load_schema_map
from core.graph import GraphManager, ProcessorBuilder
class TestConfigParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_path = '../resources'
        self.schema_map = load_schema_map(SCHEMA_PATH)

        self.stack_config_path = f'{self.resource_path}/config/stack.yaml'
        self.stack_config = read_yaml(self.stack_config_path)

    def test_graph_manager_item(self):
        graph_manager = GraphManager(self.stack_config, self.schema_map)
        self.assertEqual(list(graph_manager[0].keys()), ['name', 'ops', 'links'])
        self.assertEqual([op[0] for op in graph_manager[0]['ops']], ['input', 'read'])
        self.assertEqual(graph_manager[0]['links'], ['stack_s2_1_2'])

    def test_processor_builder_stack(self):
        graph_manager = GraphManager(self.stack_config, self.schema_map)
        processor_builder = ProcessorBuilder(graph_manager)
        end_points = processor_builder.build()
        self.assertEqual(len(end_points), 1)
