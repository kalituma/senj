import os
import unittest

from core.config import expand_var

class TestWriteOp(unittest.TestCase):
    def setUp(self) -> None:
        os.environ['PROJ_LIB'] = '/home/airs_khw/anaconda3/envs/snap/share/proj'

        self.project_path = expand_var('$PROJECT_PATH')

        self.s2_target_path = os.path.join(self.project_path, 'data', 'test', 'target')

        self.s1_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_safe_path = os.path.join(self.project_path, 'data', 'test', 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')

        self.atmos_user_conf = os.path.join(self.project_path, 'test', 'resources', 'config', 'atmos', 'S2A_MSI.txt')