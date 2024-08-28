import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml
from core.config import load_schema_map, expand_var
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder

class TestExecuteBasedConfigs(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resource'))
        self.schema_map = load_schema_map(SCHEMA_PATH)

    def build_and_execute(self, config):
        with Context(GraphManager(config, self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]

            for gen in gens:
                for x in gen:
                    print(x)

    def test_stack_preprocess(self):
        stack_config_path = f'{self.resource_root}/config/stack.yaml'
        stack_config = read_yaml(stack_config_path)
        self.build_and_execute(stack_config)
    def test_s1_preprocess(self):
        s1_config_path = f'{self.resource_root}/config/s1_preprocessing.yaml'
        s1_config = read_yaml(s1_config_path)
        self.build_and_execute(s1_config)
