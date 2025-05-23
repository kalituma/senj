import unittest, os

from core import SCHEMA_PATH
from core.util import read_yaml, Logger
from core.config import load_schema_map, expand_var
from test.global_test.config_test import executeGraph

class TestReadWriteConfigExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
        log_path = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'target', 'test_out', 'read_write_config', 'read_write_config.log'))
        Logger.get_logger(log_level='info', log_file_path=log_path)
        self.schema_map = load_schema_map(SCHEMA_PATH)

    def test_read_write_single_safe(self):
        config_path = f'{self.resource_root}/config/read_write/simple_read_write.yaml'
        executeGraph(config_path, self.schema_map)

    def test_read_write_dim_multiple(self):
        config_path = f'{self.resource_root}/config/read_write/multiple_read_write.yaml'
        executeGraph(config_path, self.schema_map)

    def test_read_write_gdal_multiple(self):
        config_path = f'{self.resource_root}/config/read_write/multiple_gdal_read_write.yaml'
        executeGraph(config_path, self.schema_map)

