import os, unittest
from core.config import expand_var
from core.raster.funcs import read_band_from_raw

class TestConverOp(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_tif_snap_path = os.path.join(self.data_root, 'tif', 's1', 'snap', 'src_1', 'terrain_corrected_0.tif')

    def test_convert_op(self):
        from core.operations import Read, Convert
        from core.logic.context import Context

        with self.subTest(msg='snap to gdal'):
            s1_raster = Read(module='snap', bands=['Sigma0_VV'])(self.s1_dim_path, Context())
            loaded_s1_raster = read_band_from_raw(s1_raster, selected_band=s1_raster.selected_bands)
            self.assertEqual(loaded_s1_raster.get_cached_band_names(), ['Sigma0_VV'])
            s1_raster = Convert(to_module='gdal')(loaded_s1_raster, Context())
            self.assertEqual(s1_raster.module_type.__str__(), 'gdal')
            self.assertEqual(s1_raster.get_band_names(), ['Sigma0_VV'])
            self.assertEqual(s1_raster.get_cached_band_names(), None)
            self.assertEqual(s1_raster.is_band_cached, False)

        with self.subTest(msg='gdal to snap'):
            s1_raster = Read(module='gdal', bands=['band_1'])(self.s1_tif_snap_path, Context())
            loaded_s1_raster = read_band_from_raw(s1_raster, selected_band=s1_raster.selected_bands)
            self.assertEqual(loaded_s1_raster.get_cached_band_names(), ['band_1'])
            s1_raster = Convert(to_module='snap')(loaded_s1_raster, Context())
            self.assertEqual(s1_raster.module_type.__str__(), 'snap')
            self.assertEqual(s1_raster.get_band_names(), ['band_1'])
            self.assertEqual(s1_raster.get_cached_band_names(), None)
            self.assertEqual(s1_raster.is_band_cached, False)