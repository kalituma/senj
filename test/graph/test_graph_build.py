import unittest, os

from core import SCHEMA_PATH
from core.util import PathType, read_yaml
from core.config import expand_var, load_schema_map
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder

class TestConfigParsing(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resource'))
        self.schema_map = load_schema_map(SCHEMA_PATH)

        self.stack_config_path = f'{self.resource_root}/config/stack.yaml'
        self.stack_config = read_yaml(self.stack_config_path)

        self.s1_config_path = f'{self.resource_root}/config/s1_write.yaml'
        self.s1_config = read_yaml(self.s1_config_path)

    def test_graph_manager_item(self):
        with self.subTest(msg='stack.yaml'):
            graph_manager = GraphManager(self.stack_config, self.schema_map)
            self.assertEqual(graph_manager.get_proc(0).ops['ops_order'], ['input', 'read'])
            self.assertEqual(graph_manager.get_proc(0).links, ['stack_s2_1_2'])

        with self.subTest(msg='s1'):
            graph_manager = GraphManager(self.s1_config, self.schema_map)
            self.assertEqual(graph_manager.get_proc(0).ops['ops_order'], ['input', 'read', 'apply_orbit', 'calibrate', 'terrain_correction'])
            self.assertEqual(graph_manager.get_proc(0).links, [])



