import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml, Logger

from core.config import load_schema_map, expand_var
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder

class TestS2RelatedConfigs(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
        self.out_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'target', 'test_out'))
        Logger.get_logger('debug', f'{self.out_data_root}/warp_chaining/log.txt')
        self.schema_map = load_schema_map(SCHEMA_PATH)

    def executeGraph(self, config_path):
        out_path = []

        with Context(GraphManager(read_yaml(config_path), self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]
            for gen in gens:
                for x in gen:
                    out_path.append(x)

        return out_path

    def test_simple_warp_chaining(self):
        stack_config_path = f'{self.resource_root}/config/warp_chaining/simple_warp_chaining.yaml'
        self.executeGraph(stack_config_path)

    def test_simple_subset_chaining(self):
        stack_config_path = f'{self.resource_root}/config/warp_chaining/simple_warp_chaining_2.yaml'
        self.executeGraph(stack_config_path)
    def test_simple_single_subset(self):
        stack_config_path = f'{self.resource_root}/config/warp_chaining/simple_single_warp.yaml'
        self.executeGraph(stack_config_path)

    def test_multiple_warp(self):
        stack_config_path = f'{self.resource_root}/config/warp_chaining/multiple_warp_chaining_with_stack.yaml'
        self.executeGraph(stack_config_path)