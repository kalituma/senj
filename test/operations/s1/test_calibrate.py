import os
import unittest

from core.operations import Read, Write
from core.operations.s1 import Calibrate
from core.raster.gpf_module import read_gpf_bands_as_dict

from core.logic.context import Context

class TestCalibrate(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = '../../resources/data'
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1','S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')

    def test_calibrate(self):
        context = Context()
        with self.subTest('try to open and calibrate'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = Calibrate()(raster, context)

        with self.subTest('try to open and calibrate with pols'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(selectedPolarisations=['VV'])(raster, context)



        with self.subTest('try to open and calibrate and image scale in db'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            raster = Calibrate(selectedPolarisations=['VV'], outputImageInComplex=True, outputImageScaleInDb=True)(raster, context)

    def test_calibrate_with_all_options(self):
        context = Context()
        raster = Read(module='snap')(self.s1_safe_slc_path, context)
        raster = Calibrate(selectedPolarisations=['VV'], outputSigmaBand=True, outputBetaBand=True, outputGammaBand=True)(raster, context)
        result, selected_band = read_gpf_bands_as_dict(raster.raw)
        self.assertEqual(len(selected_band), 3)
        self.assertEqual(selected_band, ['Sigma0_VV', 'Beta0_VV', 'Gamma0_VV'])

    def test_calibrate_in_complex(self):
        context = Context()
        raster = Read(module='snap')(self.s1_safe_slc_path, context)
        raster = Calibrate(selectedPolarisations=['VV'], outputImageInComplex=True)(raster, context)
        result, selected_band = read_gpf_bands_as_dict(raster.raw)
        self.assertEqual(selected_band, ['i_IW1_VV', 'q_IW1_VV', 'Intensity_IW1_VV', 'i_IW2_VV', 'q_IW2_VV', 'Intensity_IW2_VV', 'i_IW3_VV', 'q_IW3_VV', 'Intensity_IW3_VV'])

    def test_calibrate_fail(self):
        context = Context()
        with self.subTest('try to calibrate with wrong pols'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            with self.assertRaises(AssertionError):
                raster = Calibrate(selectedPolarisations=['XX'])(raster, context)




