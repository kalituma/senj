import os
import unittest
from lxml import objectify, etree

from core.config import expand_var
from core.util import ProductType
from core.util.atmos import identify_product


class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = expand_var('$PROJECT_PATH')
        self.test_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')

        input_dir = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'split_safe')

        self.s1_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s1_safe_grdh_path = os.path.join(self.test_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_slc_path = os.path.join(self.test_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')

        self.s2_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's2', 'snap',
                                        'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s2_safe_path = os.path.join(self.test_root, 'safe', 's2',
                                         'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

        self.meta_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/senj/data/test/safe/s1/S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE/annotation/s1b-iw1-slc-vh-20190807t213153-20190807t213218-017485-020e22-001.xml'
        self.wv_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF'
        self.ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'
        self.ps_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/10.PlanetScope_20190403_강릉/20190403_04_Radiance/files/20190403_005542_1_0f3c_3B_AnalyticMS_clip.tif'

    def test_read_xml(self):
        root = etree.parse(self.meta_path).getroot()
        self.assertEqual(root.xpath('//missionId/text()')[0], 'S1B')
        print()

    def test_identify(self):

        with self.subTest(msg='SAFE test'):
            type = identify_product(self.s1_safe_grdh_path)
            self.assertEqual(type, ProductType.S1)
            type = identify_product(self.s2_safe_path)
            self.assertEqual(type, ProductType.S2)
            type = identify_product(self.s1_slc_path)
            self.assertEqual(type, ProductType.S1)

        with self.subTest(msg='DIM test'):
            type = identify_product(self.s1_dim_path)
            self.assertEqual(type, ProductType.S1)
            type = identify_product(self.s2_dim_path)
            self.assertEqual(type, ProductType.S2)

        with self.subTest(msg='Worldview test'):
            type = identify_product(self.wv_path)
            self.assertEqual(type, ProductType.WV)
            type = identify_product(os.path.dirname(self.wv_path))
            self.assertEqual(type, ProductType.UNKNOWN)
            type = identify_product(self.ge_path)
            self.assertEqual(type, ProductType.WV)

        with self.subTest(msg='Planet test'):
            type = identify_product(self.ps_path)

