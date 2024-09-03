import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder
from core.operations import Read
from core.config import load_schema_map, expand_var

class TestMergeConfigExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
        self.schema_map = load_schema_map(SCHEMA_PATH)

    def test_read_write_single_safe(self):
        config_path = f'{self.resource_root}/config/read_cached_merge/multiple_cached_merge_strict.yaml'

        out_path = []
        with Context(GraphManager(read_yaml(config_path), self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]
            for gen in gens:
                for x in gen:
                    out_path.append(x)

        for path in out_path:
            result_raster = Read(module='snap')(path)
            print()



    def test_read_merge_config_simple(self):
        config_path = f'{self.resource_root}/config/read_cached_merge/simple_read_stack_strict.yaml'

        out_path = []
        with Context(GraphManager(read_yaml(config_path), self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]
            for gen in gens:
                for x in gen:
                    out_path.append(x)

            for path in out_path:
                result_raster = Read(module='snap')(path, ctx)
                self.assertEqual(result_raster.get_band_names(), ['B2', 'B3', 'B4', 'B2_1', 'B3_1', 'B4_1'])