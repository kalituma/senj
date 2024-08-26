import os
import unittest

from core.config import expand_var
from core.operations import Write, Read
from core.logic import Context

class TestWriteOp(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_grdh_path = os.path.join(self.test_data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_dim_path = os.path.join(self.test_data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.test_data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_safe_slc_path = os.path.join(self.test_data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.test_data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

        self.wv_xml_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL','19APR04021253-M2AS-014493935010_01_P001.XML')
        self.wv_tif_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL','19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF')

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

    def test_write_safe_op(self):
        with self.subTest('write_s1_safe_using_snap'):
            context = Context(None)
            read = Read(module='SNAP', bword='*_VV', bname_word_included=True)
            safe_raster = read(self.s1_safe_grdh_path, context)
            self.assertEqual(safe_raster.get_band_names(), ['Amplitude_VV', 'Intensity_VV'])

            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='s1_safe_out', out_ext='dim', bands=['Intensity_VV'])(safe_raster)
            result = Read(module='SNAP')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['Intensity_VV'])
    def test_write_dim_op(self):
        with self.subTest('write_s1_dim_using_snap'):
            context = Context(None)
            read = Read(module='SNAP', bword='*', bname_word_included=True)
            dim_raster = read(self.s1_dim_path, context)
            self.assertEqual(dim_raster.get_band_names(), ['Sigma0_VV'])

            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='s1_dim_out', out_ext='dim')(dim_raster)
            result = Read(module='SNAP')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['Sigma0_VV'])

    def test_write_world_view(self):
        context = Context(None)

        with self.subTest('write_wv_xml_using_snap'):
            wv_raster = Read(module='SNAP', bands=['BAND_R', 'BAND_N'])(self.wv_xml_path, context)
            self.assertEqual(wv_raster.get_band_names(), ['BAND_R', 'BAND_N'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='wv_xml_out', out_ext='tif', bands=['BAND_R'])(wv_raster)
            result = Read(module='SNAP')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['BAND_R'])

        with self.subTest('write_wv_tif_using_gdal'):
            wv_raster = Read(module='gdal', bword='BAND*', bname_word_included=True)(self.wv_tif_path, context)
            self.assertEqual(wv_raster.get_band_names(), ['BAND_B', 'BAND_G', 'BAND_R', 'BAND_N'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='wv_tif_out', out_ext='tif', bands=['BAND_R'])(wv_raster)
            result = Read(module='SNAP')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['BAND_R'])

    def test_write_geo_eye(self):
        context = Context(None)
        with self.subTest('write_ge_xml_using_gdal'):
            ge_raster = Read(module='gdal', bands=['BAND_R', 'BAND_N'])(self.ge_xml_path, context)
            self.assertEqual(ge_raster.get_band_names(), ['BAND_R', 'BAND_N'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='ge_xml_out', out_ext='tif', bands=['BAND_R'])(ge_raster)
            result = Read(module='gdal')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['BAND_R'])

        with self.subTest('write_ge_xml_using_gdal'):
            ge_raster = Read(module='snap', bands=['BAND_R', 'BAND_N'])(self.ge_tif_path, context)
            self.assertEqual(ge_raster.get_band_names(), ['BAND_R', 'BAND_N'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='ge_tif_out', out_ext='dim', bands=['BAND_R'])(ge_raster)
            result = Read(module='snap')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['BAND_R'])

    def test_write_planet_scope(self):
        context = Context(None)
        with self.subTest('write_ps_xml_using_gdal'):
            ps_raster = Read(module='gdal', bands=['band_3', 'band_2'])(self.ps_xml_path, context)
            self.assertEqual(ps_raster.get_band_names(), ['band_3', 'band_2'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='ps_xml_out', out_ext='tif', bands=['band_3'])(ps_raster)
            result = Read(module='gdal')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['band_3'])

        with self.subTest('write_ps_tif_using_snap'):
            ps_raster = Read(module='snap', bands=['band_3', 'band_2'])(self.ps_tif_path, context)
            self.assertEqual(ps_raster.get_band_names(), ['band_3', 'band_2'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='ps_tif_out', out_ext='dim', bands=['band_3'])(ps_raster)
            result = Read(module='snap')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['band_3'])

    def test_tif_no_metadata(self):
        context = Context(None)

        with self.subTest('write_s2_without_meta'):
            s2_raster = Read(module='gdal', bands=['band_5', 'band_4', 'band_3'])(self.s2_without_meta, context)
            self.assertEqual(s2_raster.get_band_names(), ['band_5', 'band_4', 'band_3'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='s2_without_meta_out', out_ext='tif', bands=['band_5'])(s2_raster)
            result = Read(module='gdal')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['band_5'])

        with self.subTest('write_s2_withoud_meta_snap'):
            s2_raster = Read(module='snap', bands=['band_5', 'band_4', 'band_3'])(self.s2_without_meta, context)
            self.assertEqual(s2_raster.get_band_names(), ['band_5', 'band_4', 'band_3'])
            out_dir = os.path.join(self.test_data_root, 'target', 'test_out')
            out_result_path = Write(out_dir=out_dir, out_stem='s2_without_meta_out_snap', out_ext='dim', bands=['band_3'])(s2_raster)
            result = Read(module='snap')(out_result_path, context)
            self.assertEqual(result.get_band_names(), ['band_3'])