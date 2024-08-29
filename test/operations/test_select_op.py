import os, unittest
from core.util import expand_var
from core.operations import Read, Select, Write
from core.logic import Context
class TestReproject(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_dim_path = os.path.join(self.test_data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_tif_path = os.path.join(self.test_data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')

    def test_select_op(self):
        context = Context(None)

        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'select_op')
        with self.subTest(msg='select using index'):
            s2_raster = Read(module='snap')(self.s2_dim_path, context)
            s2_raster = Select(bands=[2, 3, 4])(s2_raster, context)
            self.assertEqual(s2_raster.get_band_names(), ['B2', 'B3', 'B4'])

        with self.subTest(msg='select using snap'):
            s2_raster = Read(module='snap')(self.s2_dim_path, context)
            s2_raster = Select(bands=['B2', 'B3', 'B4', 'view_zenith_B2'])(s2_raster, context)
            # Write(out_dir=out_dir, out_stem='select_snap', out_ext='dim')(s2_raster, context)

        with self.subTest(msg='select using gdal'):
            s1_raster = Read(module='gdal')(self.s1_tif_path, context)
            s1_raster = Select(bands=['B2', 'B3', 'B4'])(s1_raster, context)
            # Write(out_dir=out_dir, out_stem='select_gdal', out_ext='tif')(s1_raster, context)