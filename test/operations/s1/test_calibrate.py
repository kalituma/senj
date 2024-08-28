import os
import unittest

from core.config import expand_var
from core.operations import Read
from core.operations.s1 import Calibrate
from core.util.snap import read_gpf_bands_as_dict
from core.util.errors import ProductTypeError, ExtensionError, ModuleError

from core.logic.context import Context

class TestCalibrate(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1','S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s1_tif_path = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')

    def test_calibrate(self):
        context = Context(None)
        with self.subTest('try to open and calibrate'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = Calibrate(outputSigmaBand=True, outputBetaBand=True, outputGammaBand=True)(raster, context)
            self.assertEqual(raster.get_band_names(), ['Sigma0_VV', 'Gamma0_VV', 'Beta0_VV', 'Sigma0_VH', 'Gamma0_VH', 'Beta0_VH'])

        with self.subTest('try to open and calibrate with pols'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(selectedPolarisations=['VV'])(raster, context)
            self.assertEqual(raster.get_band_names(), ['Sigma0_IW1_VV', 'Sigma0_IW2_VV', 'Sigma0_IW3_VV'])

        with self.subTest('try to open and calibrate with pols and complex options'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(selectedPolarisations=['VV'], outputImageInComplex=True)(raster, context)
            self.assertEqual(raster.get_band_names(),
                             ['i_IW1_VV', 'q_IW1_VV', 'Intensity_IW1_VV', 'i_IW2_VV', 'q_IW2_VV', 'Intensity_IW2_VV', 'i_IW3_VV', 'q_IW3_VV', 'Intensity_IW3_VV'])

        with self.subTest('try to open and calibrate with pols and scale options'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(selectedPolarisations=['VV'], outputImageScaleInDb=True)(raster, context)
            self.assertEqual(raster.get_band_names(), ['Sigma0_IW1_VV', 'Sigma0_IW2_VV', 'Sigma0_IW3_VV'])


        with self.subTest('try to open and calibrate and image scale in db'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(selectedPolarisations=['VV'], outputSigmaBand=True, outputBetaBand=True,
                               outputImageInComplex=True, outputImageScaleInDb=True)(raster, context)

    def test_calibrate_with_all_options(self):
        context = Context(None)
        raster = Read(module='snap')(self.s1_safe_slc_path, context)
        raster = Calibrate(selectedPolarisations=['VV'], outputSigmaBand=True, outputBetaBand=True, outputGammaBand=True)(raster, context)
        result, selected_band = read_gpf_bands_as_dict(raster.raw)
        self.assertEqual(len(selected_band), 3)
        self.assertEqual(selected_band, ['Sigma0_VV', 'Beta0_VV', 'Gamma0_VV'])

    def test_calibrate_in_complex(self):
        context = Context(None)
        raster = Read(module='snap')(self.s1_safe_slc_path, context)
        raster = Calibrate(selectedPolarisations=['VV'], outputImageInComplex=True)(raster, context)
        result, selected_band = read_gpf_bands_as_dict(raster.raw)
        self.assertEqual(selected_band, ['i_IW1_VV', 'q_IW1_VV', 'Intensity_IW1_VV', 'i_IW2_VV', 'q_IW2_VV', 'Intensity_IW2_VV', 'i_IW3_VV', 'q_IW3_VV', 'Intensity_IW3_VV'])

    def test_calibrate_fail(self):
        context = Context(None)
        with self.subTest('try to calibrate with wrong pols'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            with self.assertRaises(AssertionError):
                raster = Calibrate(selectedPolarisations=['XX'])(raster, context)

    def test_wrong_input(self):
        context = Context(None)
        with self.subTest('try to calibrate with wrong input'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(ProductTypeError):
                raster = Calibrate(outputSigmaBand=True, outputBetaBand=True, outputGammaBand=True)(raster, context)

        with self.subTest('try to calibrate with wrong extension file'):
            raster = Read(module='snap')(self.s1_dim_path, context)
            with self.assertRaises(ExtensionError):
                raster = Calibrate(selectedPolarisations=['VV'])(raster, context)

        with self.subTest('try to calibrate with wrong module'):
            raster = Read(module='gdal')(self.s1_tif_path, context)
            with self.assertRaises(ModuleError):
                raster = Calibrate(selectedPolarisations=['VV'])(raster, context)




