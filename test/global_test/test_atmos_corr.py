import unittest, os

from core import SCHEMA_PATH
from core.util import Logger
from core.config import load_schema_map, expand_var
from test.global_test.config_test import executeGraph


class TestS2RelatedConfigs(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_root = expand_var(os.path.join('$PROJECT_PATH', 'test', 'resources'))
        self.out_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test', 'target', 'test_out'))
        Logger.get_logger('info', f'{self.out_data_root}/warp_chaining/log.txt')
        self.schema_map = load_schema_map(SCHEMA_PATH)

    def test_simple_atmos_corr(self):
        stack_config_path = f'{self.resource_root}/config/read_cached_merge/simple_atmos_corr_subset.yaml'
        executeGraph(stack_config_path, self.schema_map)
