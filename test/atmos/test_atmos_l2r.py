import os
import unittest
import copy

import core.atmos as atmos
from core.atmos.setting import parse
from core.atmos.run import set_l2w_and_polygon

from core.util import expand_var
from core.atmos.run import apply_l2r, set_earthdata_login_to_env, write_map
from core.util import write_pickle, read_pickle, get_files_recursive

class TestAtmosL2R(unittest.TestCase):
    def setUp(self):
        self.project_path = expand_var('$PROJECT_PATH')
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')
        self.l1r_dir = os.path.join(self.target_path, 's2', 'l1r_out')
        self.l2r_dir = os.path.join(self.target_path, 's2', 'l2r_out')
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

        atmos.settings['user'] = parse(sensor=global_attrs['sensor'], merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
        set_earthdata_login_to_env(atmos.settings['run'])

        l2r_global_attrs = copy.deepcopy(global_attrs)
        l2r, l2r_global_attrs = apply_l2r(l1r, l2r_global_attrs)

        self.do_write_map(l2r, out_dir=self.l2r_dir, out_file_stem='l2r_out.dim', global_attrs=l2r_global_attrs)
        write_pickle(l2r, os.path.join(self.l2r_dir, 'l2r_out.dim.pkl'))
        write_pickle(global_attrs, os.path.join(self.l2r_dir, 'l2r_global_attrs.dim.pkl'))

    def test_l2r_wv(self):
        # ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'

        l1r_path = os.path.join(self.l1r_dir, 'l1r_out.wv.pkl')
        l1r = read_pickle(l1r_path)
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.wv.pkl')
        global_attrs = read_pickle(global_attrs_path)

        atmos.settings['user'] = parse(sensor=global_attrs['sensor'], merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
        set_earthdata_login_to_env(atmos.settings['run'])

        l2r_global_attrs = copy.deepcopy(global_attrs)
        l2r, l2r_global_attrs = apply_l2r(l1r, l2r_global_attrs)

        self.do_write_map(l2r, out_dir=self.l2r_dir, out_file_stem='l2r_out.wv', global_attrs=l2r_global_attrs)
        write_pickle(l2r, os.path.join(self.l2r_dir, 'l2r_out.wv.pkl'))
        write_pickle(global_attrs, os.path.join(self.l2r_dir, 'l2r_global_attrs.wv.pkl'))

    def test_l2r_ge(self):
        # ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'

        l1r_path = os.path.join(self.l1r_dir, 'l1r_out.ge.pkl')
        l1r = read_pickle(l1r_path)
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.ge.pkl')
        global_attrs = read_pickle(global_attrs_path)

        atmos.settings['user'] = parse(sensor=global_attrs['sensor'], merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
        set_earthdata_login_to_env(atmos.settings['run'])

        l2r_global_attrs = copy.deepcopy(global_attrs)
        l2r, l2r_global_attrs = apply_l2r(l1r, l2r_global_attrs)

        self.do_write_map(l2r, out_dir=self.l2r_dir, out_file_stem='l2r_out.ge', global_attrs=l2r_global_attrs)
        write_pickle(l2r, os.path.join(self.l2r_dir, 'l2r_out.ge.pkl'))
        write_pickle(global_attrs, os.path.join(self.l2r_dir, 'l2r_global_attrs.ge.pkl'))

    def test_l2r_ps(self):
        # ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'

        l1r_path = os.path.join(self.l1r_dir, 'l1r_out.ps.snap.pkl')
        l1r = read_pickle(l1r_path)
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.ps.snap.pkl')
        global_attrs = read_pickle(global_attrs_path)

        atmos.settings['user'] = parse(sensor=global_attrs['sensor'], merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
        set_earthdata_login_to_env(atmos.settings['run'])

        l2r_global_attrs = copy.deepcopy(global_attrs)
        l2r, l2r_global_attrs = apply_l2r(l1r, l2r_global_attrs)

        self.do_write_map(l2r, out_dir=self.l2r_dir, out_file_stem='l2r_out.ps', global_attrs=l2r_global_attrs)
        write_pickle(l2r, os.path.join(self.l2r_dir, 'l2r_out.ps.pkl'))
        write_pickle(global_attrs, os.path.join(self.l2r_dir, 'l2r_global_attrs.ps.pkl'))

    def do_write_map(self, data_dict, out_dir, out_file_stem, global_attrs):
        map_settings = {'rgb_rhot': False, 'rgb_rhorc': False, 'rgb_rhos': True, 'rgb_rhow': False}
        map_settings = atmos.setting.parse(None, settings=map_settings, merge=False)

        write_map(data_dict, out_settings=map_settings, out_file_stem=out_file_stem, out_dir=out_dir, global_attrs=global_attrs)