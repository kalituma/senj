import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder
from core.config import load_schema_map, expand_var

class TestExecuteBasedConfigs(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
        self.schema_map = load_schema_map(SCHEMA_PATH)

    def test_read_write_single_safe(self):
        config_path = f'{self.resource_root}/config/read_write/simple_read_write.yaml'

        with Context(GraphManager(read_yaml(config_path), self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]
            for gen in gens:
                for x in gen:
                    print(x)

    def test_read_write_dim_multiple(self):
        config_path = f'{self.resource_root}/config/read_write/multiple_read_write.yaml'

        with Context(GraphManager(read_yaml(config_path), self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]
            for gen in gens:
                for x in gen:
                    print(x)

    def test_read_write_gdal_multiple(self):
        config_path = f'{self.resource_root}/config/read_write/multiple_gdal_read_write.yaml'

        with Context(GraphManager(read_yaml(config_path), self.schema_map)) as ctx:
            processor_builder = ProcessorBuilder(ctx)
            end_points = processor_builder.build()
            gens = [end_point.execute() for end_point in end_points]
            for gen in gens:
                for x in gen:
                    print(x)

