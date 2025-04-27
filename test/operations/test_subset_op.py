import os, unittest

from core.logic import Context
from core.util import expand_var, Logger
from core.operations import Read, RasterClip, Write
class TestSubset(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))

        self.s2_1_safe_path = os.path.join(self.test_data_root, 'safe', 's2_list', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_2_safe_path = os.path.join(self.test_data_root, 'safe', 's2_list', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDE_20230509T035526.SAFE')
        self.s2_snap_tif = os.path.join(self.test_data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')


    def test_subset(self):
        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'subset_op')
        with self.subTest(msg='subset with bounds'):
            context = Context(None)
            snap_tif_raster = Read(module='snap')(self.s2_snap_tif, context)
            snap_tif_raster = RasterClip(bounds=[128.252, 34.9448, 128.3277, 34.8775])(snap_tif_raster, context)
            print(Write(out_dir=out_dir, out_stem='test_out', suffix='subset', out_ext='tif')(snap_tif_raster, context))

        with self.subTest(msg='subset with bounds in different projection'):
            context = Context(None)
            snap_tif_raster = Read(module='snap')(self.s2_safe_path, context)
            snap_tif_raster = RasterClip(bounds=[128.252, 34.9448, 128.3277, 34.8775], copyMetadata=False)(snap_tif_raster, context)
            print(Write(out_dir=out_dir, out_stem='test_out', suffix='subset_with_grid_points', out_ext='dim')(snap_tif_raster, context))

    def test_safe_subset_for_input(self):
        out_dir = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/dim/'
        Logger.get_logger(log_file_path=out_dir + 'subset_op.log')
        context = Context(None)
        with self.subTest(msg='subset with bounds'):
            snap_tif_raster = Read(module='snap')(self.s2_1_safe_path, context)
            subset_op = RasterClip(bounds=[412290, 3914633, 476647, 3869088], bounds_epsg=32652, copy_meta=True)
            subset_op.module_type = 'snap'
            snap_tif_raster = subset_op(snap_tif_raster, context)
            print(Write(out_dir=out_dir, out_stem='S2A_MSIL1C_20230509T020651_SDD', suffix='subset', out_ext='dim')(snap_tif_raster, context))

            snap_tif_raster = Read(module='snap')(self.s2_2_safe_path, context)
            subset_op =RasterClip(bounds=[421531, 3919583, 479618, 3866777], bounds_epsg=32652, copy_meta=True)
            subset_op.module_type = 'snap'
            snap_tif_raster = subset_op(snap_tif_raster, context)

            print(Write(out_dir=out_dir, out_stem='S2A_MSIL1C_20230509T020651_SDE', suffix='subset', out_ext='dim')(
                snap_tif_raster, context))
