import os, unittest

from core.logic import Context
from core.util import expand_var

from core.operations import Read
from core.operations.s1 import Calibrate, ApplyOrbit, TopsarDeburst, TerrainCorrection

class TestConstraint(unittest.TestCase):
    def setUp(self):
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_slc_path = os.path.join(self.test_data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s1_safe_grdh_path = os.path.join(self.test_data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')

        self.s1_dim_path = os.path.join(self.test_data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.test_data_root, 'dim', 's2', 'snap',
                                        'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s2_safe_path = os.path.join(self.test_data_root, 'safe', 's2',
                                         'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

        self.wv_xml_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS-014493935010_01_P001.XML')
        self.wv_tif_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF')

        self.ge_tif_path = os.path.join(self.test_data_root, 'tif', 'ge', '014493907010_01_P001_MUL',
                                        '19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF')
        self.ge_xml_path = os.path.join(self.test_data_root, 'tif', 'ge', '014493907010_01_P001_MUL',
                                        '19APR07023734-M2AS-014493907010_01_P001.XML')

        self.ps_tif_path = os.path.join(self.test_data_root, 'tif', 'ps', '20190817_Radiance', 'files',
                                        '20200817_013159_78_2277_3B_AnalyticMS_clip.tif')
        self.ps_xml_path = os.path.join(self.test_data_root, 'tif', 'ps', '20190817_Radiance', 'files',
                                        '20200817_013159_78_2277_3B_AnalyticMS_metadata_clip.xml')

        self.s1_tif_snap_path = os.path.join(self.test_data_root, 'tif', 's1', 'snap', 'src_1',
                                             'terrain_corrected_0.tif')
        self.s2_tif_snap_path = os.path.join(self.test_data_root, 'tif', 's2', 'snap',
                                             'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')
        self.s1_tif_gdal_path = os.path.join(self.test_data_root, 'tif', 's1', 'gdal', 'src_1',
                                             'terrain_corrected_0.tif')
        self.s2_tif_gdal_path = os.path.join(self.test_data_root, 'tif', 's2', 'gdal', 'out_0_read.tif')
        self.s2_without_meta = os.path.join(self.test_data_root, 's2merge_1_stack_subset.tif')

    def test_calibrate(self):
        context = Context(None)
        with self.subTest('try to open and calibrate'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = Calibrate()(raster, context)

        with self.subTest('try to open and calibrate with pols'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(polarisations=['VV'])(raster, context)

        with self.subTest('try to open and calibrate and image scale in db'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(polarisations=['VV'], output_in_complex=True, output_in_db=True)(raster, context)