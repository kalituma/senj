import os
import unittest

import core.atmos as atmos
from core.atmos.setting import parse
from core.atmos.run import set_l2w_and_polygon

from core.util import expand_var
from core.util import read_pickle

class TestAtmosRGB(unittest.TestCase):
    def setUp(self):
        self.project_path = expand_var('$PROJECT_PATH')
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')
        self.l1r_dir = os.path.join(self.target_path, 's2', 'l1r_out')
        self.l2r_dir = os.path.join(self.target_path, 's2', 'l2r_out')

        self.atmos_user_conf = os.path.join(self.project_path, 'test', 'resources', 'config', 'atmos', 'S2A_MSI.txt')

        self.s2_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's2', 'snap',
                                        'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')

    def test_write_rgb(self):
        l1r_path = os.path.join(self.l1r_dir, 'l1r_out.full.dim.pkl')
        l1r = read_pickle(l1r_path)
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.full.dim.pkl')
        global_attrs = read_pickle(global_attrs_path)

        atmos.settings['user'] = parse(None, self.atmos_user_conf, merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])

        if atmos.settings['run']['map_l1r'] or atmos.settings['run']['rgb_rhot']:
            print()
