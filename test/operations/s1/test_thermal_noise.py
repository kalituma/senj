import os
import unittest
import numpy as np

from core.util import expand_var
from core.operations import Read, Write, RasterClip
from core.operations.s1 import ThermalNoiseRemoval
from core.util.errors import ProductTypeError
from core.logic.context import Context


class TestThermalNoise(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s1_tif_path = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')

    def test_thermal_noise(self):
        context = Context(None)
        out_dir = os.path.join(self.data_root, 'target', 'test_out', 's1_thermal_op')
        with self.subTest('try to open and remove thermal noise from s1 grdh product'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = ThermalNoiseRemoval()(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='thermal_noise_removal', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV', 'Intensity_VH'])

    def test_thermal_noise_with_pols(self):
        context = Context(None)
        out_dir = os.path.join(self.data_root, 'target', 'test_out', 's1_thermal_op')
        with self.subTest('try to open and remove thermal noise from s1 grdh product with polarisations'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = ThermalNoiseRemoval(polarisations=['VV'])(raster, context)
            # out_path = Write(out_dir=out_dir, out_stem='s1', suffix='thermal_noise_removal', out_ext='dim')(raster)
            self.assertEqual(raster.get_band_names(), ['Intensity_VV'])

    def test_thermal_noise_fail(self):
        context = Context(None)
        with self.subTest('try to open and remove thermal noise from s2 product'):
            raster = Read(module='snap')(self.s2_safe_path, context)
            with self.assertRaises(ProductTypeError):
                raster = ThermalNoiseRemoval()(raster, context)