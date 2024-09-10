import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml, Logger

from core.config import load_schema_map, expand_var
class TestS1UsingSnap(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
        self.out_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'target', 'test_out'))
        Logger.get_logger('debug', f'{self.out_data_root}/warp_chaining/log.txt')
        self.schema_map = load_schema_map(SCHEMA_PATH)

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