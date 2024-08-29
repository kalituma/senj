import os
import unittest

from core.util import expand_var
# from core.atmos.run import apply_atmos

class TestAtmosL2R(unittest.TestCase):
    def setUp(self):
        self.project_path = expand_var('$PROJECT_PATH')
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')
        self.l1r_dir = os.path.join(self.target_path, 's2', 'l1r_out')
        self.l2r_dir = os.path.join(self.target_path, 's2', 'l2r_out')
