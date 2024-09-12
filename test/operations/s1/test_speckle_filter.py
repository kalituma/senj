import os
import unittest
import numpy as np

from core.util import expand_var, Logger
from core.operations import Read, Write, Subset
from core.operations.s1 import SpeckleFilter
from core.util.errors import ProductTypeError
from core.logic.context import Context

class TestSpeckleFilter(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s1_tif_path = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')

    def test_speckle_filter(self):
        context = Context(None)

        out_dir = os.path.join(self.data_root, 'target', 'test_out', 's1_speckle_op')
        Logger.get_logger(log_level='debug', log_file_path=os.path.join(out_dir, 'speckle_filter.log'))
        with self.subTest('try to open and apply speckle filter to s1 grdh product'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(filter='LEE_REFINED')(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Amplitude_VV', 'Intensity_VV', 'Amplitude_VH', 'Intensity_VH'])

        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=[1])(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Amplitude_VV'])

        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'])(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_sepck_filter_with_filter(self):

        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], filter='Lee Sigma')(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], filter='Frost')(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_damping_factor(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], damping_factor=3)(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_filter_size(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], filter_size=(5, 5))(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_number_looks(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], number_looks=2)(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_window_size(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], window_size='7x7')(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_target_window_size(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], target_window_size='3x3')(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_sigma(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], sigma='0.9')(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_speckle_filter_with_an_size(self):
        context = Context(None)
        with self.subTest('try to open and apply speckle filter to s1 grdh product with polarisations and filter'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = SpeckleFilter(bands=['Intensity_VV'], an_size=60)(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='speckle_filter', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])