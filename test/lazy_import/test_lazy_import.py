import os
import unittest
from core.util import expand_var, Logger, ProductType
from core.util import import_lazy
from core.logic.context import Context
from core.operations import Read

class LazyTest(unittest.TestCase):
    def setUp(self) -> None:
        Logger.get_logger(log_level='info',
                          log_file_path='/tmp/read_op.log')

        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))

        self.wv_xml_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS-014493935010_01_P001.XML')
        self.wv_tif_path = os.path.join(self.test_data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF')

        self.ge_tif_path = os.path.join(self.test_data_root, 'tif', 'ge', '014493907010_01_P001_MUL',
                                        '19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF')
        self.ge_xml_path = os.path.join(self.test_data_root, 'tif', 'ge', '014493907010_01_P001_MUL',
                                        '19APR07023734-M2AS-014493907010_01_P001.XML')

        self.s1_tif_snap_path = os.path.join(self.test_data_root, 'tif', 's1', 'snap', 'src_1',
                                             'terrain_corrected_0.tif')
        self.s2_tif_snap_path = os.path.join(self.test_data_root, 'tif', 's2', 'snap',
                                             'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')
        self.s1_tif_gdal_path = os.path.join(self.test_data_root, 'tif', 's1', 'gdal', 'src_1',
                                             'terrain_corrected_0.tif')
        self.s2_tif_gdal_path = os.path.join(self.test_data_root, 'tif', 's2', 'gdal', 'out_0_read.tif')
        self.s2_without_meta = os.path.join(self.test_data_root, 'tif', 'no_meta', 'out_0_read.tif')

    def test_lazy_import_when_read(self):
        context = Context(None)
        with self.subTest('read snap tif'):
            Read(module='gdal')(self.s1_tif_snap_path, context)

        with self.subTest('read snap tif with band index'):
            Read(module='gdal', bands=[1])(self.s1_tif_snap_path, context)

        with self.subTest('read gdal tif'):
            Read(module='gdal')(self.s1_tif_gdal_path, context)

        with self.subTest('read gdal tif with band index'):
            Read(module='gdal', bands=[1])(self.s1_tif_gdal_path, context)

        with self.subTest('read tif not having meta using gdal'):
            result_raster = Read(module='gdal')(self.s2_without_meta, context)
            self.assertEqual(result_raster.meta_dict, None)
            self.assertEqual(result_raster.product_type, ProductType.UNKNOWN)