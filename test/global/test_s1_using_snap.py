import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml
from core.graph import GraphManager
from core.logic import Context
from core.logic.processor import ProcessorBuilder
from core.operations import Read
from core.config import load_schema_map, expand_var
class TestS1UsingSnap(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
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

    def test_s1_slc_using_snap(self):
        config_path = f'{self.resource_root}/config/s1_operations/simple_s1_slc_write.yaml'
        self.executeGraph(config_path)

    def test_s1_grdh_using_snap(self):
        config_path = f'{self.resource_root}/config/s1_operations/simple_s1_grdh_write.yaml'
        self.executeGraph(config_path)

    def test_s1_slc_grdh_stack(self):
        config_path = f'{self.resource_root}/config/s1_operations/s1_slc_grdh_stack_subset.yaml'
        self.executeGraph(config_path)

    def test_grdh_list(self):
        config_path = f'{self.resource_root}/config/s1_operations/multiple_s1_grdh_write.yaml'
        self.executeGraph(config_path)