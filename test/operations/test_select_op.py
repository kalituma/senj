import os, unittest
from pathlib import Path
from core.util import expand_var, Logger
from core.operations import Read, Select, Write, Split, MultiWrite
from core.logic import Context
class TestReproject(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.logger = Logger.get_logger('debug', os.path.join(self.test_data_root, 'target', 'test_out', 'log.txt'))
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
    def test_select_rename(self):
        context = Context(None)

        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'select_op')
        with self.subTest(msg='select using index'):
            s2_raster = Read(module='snap')(self.s2_dim_path, context)
            s2_raster = Select(bands=[2, 3, 4], band_labels=['a', 'b', 'c'])(s2_raster, context)
            self.assertEqual(s2_raster.get_band_names(), ['a', 'b', 'c'])

        with self.subTest(msg='select using gdal'):
            s1_raster = Read(module='gdal')(self.s1_tif_path, context)
            s1_raster = Select(band_labels=['a', 'b', 'c', 'aa', 'bb', 'cc'])(s1_raster, context)
            self.assertEqual(s1_raster.get_band_names(), ['a', 'b', 'c', 'aa', 'bb', 'cc'])

    def test_save_rgb(self):
        context = Context(None)
        out_root = Path('/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/NO_META')
        # get sub dir from out_root
        children = [p for p in out_root.iterdir() if p.is_dir()]
        for child in children:
            in_raster = Read(module='snap', bands=['B2', 'B3', 'B4'])(self.s2_dim_path, context)
            in_raster = Select(bands=['B2', 'B3', 'B4'], band_labels=['BLUE', 'GREEN', 'RED'])(in_raster, context)
            splitted_raster = Split()(in_raster, context)
            MultiWrite(out_dir=str(child), out_stem=child.name, out_ext='tif')(splitted_raster, context)
            # Write(out_dir=str(child), out_stem=children[0].name, out_ext='tif')(in_raster, context)



