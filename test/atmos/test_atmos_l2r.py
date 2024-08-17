import os
import unittest

import core.atmos as atmos
from core.atmos.setting import parse
from core.atmos.run import set_l2w_and_polygon

from core.config import expand_var
from core.atmos.run import apply_l2r
from core.util import write_pickle, read_pickle, get_files_recursive

class TestAtmosL2R(unittest.TestCase):
    def setUp(self):
        self.project_path = expand_var('$PROJECT_PATH')
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')
        self.l1r_dir = os.path.join(self.target_path, 's2', 'l1r_out')
        self.atmos_user_conf = os.path.join(self.project_path, 'test', 'resources', 'config', 'atmos', 'S2A_MSI.txt')
        self.s2_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        # input_dir = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'split_safe')

        # self.res_60_path = os.path.join(input_dir, 'split_safe_0_B1_B_detector_footprint_B1.tif')
        # self.res_10_path = os.path.join(input_dir, 'split_safe_1_B2_B_detector_footprint_B2.tif')
        # self.res_20_path = os.path.join(input_dir, 'split_safe_2_B6_B_detector_footprint_B6.tif')
        #
        # self.atmos_user_conf = os.path.join(self.project_path, 'test', 'resources', 'config', 'atmos', 'S2A_MSI.txt')


    def test_l2r(self):

        l1r_path = os.path.join(self.l1r_dir, 'b1_l1r_out.pkl')
        l1r = read_pickle(l1r_path)
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.pkl')
        global_attrs = read_pickle(global_attrs_path)
        # l1r_meta_path = os.path.join(self.l1r_dir, 'l1r_meta.pkl')
        # l1r_meta = read_pickle(l1r_meta_path)

        # in init_atmos
        atmos.settings['user'] = parse(None, self.atmos_user_conf, merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])

        l2r, global_attrs = apply_l2r(l1r, global_attrs)

    def test_l2r_dim(self):
        l1r_path = os.path.join(self.l1r_dir, 'l1r_out.full.dim.pkl')
        l1r = read_pickle(l1r_path)
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.full.dim.pkl')
        global_attrs = read_pickle(global_attrs_path)

        atmos.settings['user'] = parse(None, self.atmos_user_conf, merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])

        l2r = apply_l2r(l1r, global_attrs)
