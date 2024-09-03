import os, unittest
from core.util import expand_var
from core.operations import Read, Stack, Write
from core.logic import Context

class TestReproject(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_dim_path = os.path.join(self.test_data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s2_tif_path_1 = os.path.join(self.test_data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')
        self.s2_tif_path_2 = os.path.join(self.test_data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')
        self.no_meta_tif = os.path.join(self.test_data_root, 'tif', 'no_meta', 'out_0_read.tif')
        self.no_meta_with_tif_header = os.path.join(self.test_data_root, 'tif', 'no_meta_with_tif_head', 'read_select_write.0.tif')

    def test_stack_op(self):
        context = Context(None)
        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'stack_op')
        with self.subTest(msg='stack using snap'):
            s2_dim_raster = Read(module='snap')(self.s2_dim_path, context)
            s2_dim_raster.raster_from = 's2_dim'
            s2_tif_raster_1 = Read(module='gdal')(self.s2_tif_path_1, context)
            s2_tif_raster_1.raster_from = 's2_tif_1'
            s2_tif_raster_2 = Read(module='snap')(self.s2_tif_path_1, context)
            s2_tif_raster_2.raster_from = 's2_tif_2'

            s2_raster = Stack(bands_list=[['B2', 'B3'], ['B3', 'B4'], None], master_module='snap', meta_from='s2_dim')([s2_tif_raster_1, s2_dim_raster, s2_tif_raster_2], context)
            # snap_out_path = Write(out_dir=out_dir, out_stem='stack_snap_snap', out_ext='dim')(s2_raster, context)
            band_answer = ['masterProduct$B2', 'masterProduct$B3', 'slaveProduct_1$B3', 'slaveProduct_1$B4', 'slaveProduct_2$B2', 'slaveProduct_2$B3', \
                              'slaveProduct_2$B4', 'slaveProduct_2$B_detector_footprint_B2', 'slaveProduct_2$B_detector_footprint_B3', 'slaveProduct_2$B_detector_footprint_B4']
            self.assertEqual(s2_raster.get_band_names(), band_answer)
            self.assertEqual(s2_raster.meta_dict['band_to_index'], s2_raster._band_to_index)
            self.assertEqual(list(s2_raster._band_to_index.keys()), band_answer)
            self.assertEqual(list(s2_raster.meta_dict['band_to_index'].keys()), band_answer)

        with self.subTest(msg='stack using gdal'):
            s2_dim_raster = Read(module='snap')(self.s2_dim_path, context)
            s2_dim_raster.raster_from = 's2_dim'
            s2_tif_raster_1 = Read(module='gdal')(self.s2_tif_path_1, context)
            s2_tif_raster_1.raster_from = 's2_tif_1'
            s2_tif_raster_2 = Read(module='gdal')(self.s2_tif_path_1, context)
            s2_tif_raster_2.raster_from = 's2_tif_2'

            s2_raster = Stack(bands_list=[['B2', 'B3'], [3,4], ['B2', 'B4']], master_module='gdal', meta_from='s2_tif_2')([s2_tif_raster_1, s2_dim_raster, s2_tif_raster_2], context)
            # gdal_out_path = Write(out_dir=out_dir, out_stem='stack_snap_gdal', out_ext='tif')(s2_raster, context)
            # s2_gdal_in = Read(module='gdal')(gdal_out_path, context)
            band_answer = ['masterDs$B2', 'masterDs$B3', 'slaveDs1$B3', 'slaveDs1$B4', 'slaveDs2$B2', 'slaveDs2$B4']
            self.assertEqual(s2_raster.get_band_names(), band_answer)
            self.assertEqual(s2_raster.meta_dict['band_to_index'], s2_raster._band_to_index)
            self.assertEqual(list(s2_raster._band_to_index.keys()), band_answer)

    def test_stack_op_with_no_meta(self):
        context = Context(None)
        with self.subTest(msg='stack using snap with no meta'):
            s2_no_meta_raster_1 = Read(module='gdal')(self.no_meta_tif, context)
            s2_no_meta_raster_1.raster_from = 's2_tif_1'
            s2_no_meta_with_header_raster_2 = Read(module='snap')(self.no_meta_with_tif_header, context)
            s2_no_meta_with_header_raster_2.raster_from = 's2_tif_2'
            s2_dim_raster = Read(module='snap')(self.s2_dim_path, context)
            s2_dim_raster.raster_from = 's2_dim'


            s2_raster = Stack(bands_list=[None, None, ['B2', 'B4']], master_module='gdal', meta_from='s2_tif_2')\
                ([s2_no_meta_raster_1, s2_no_meta_with_header_raster_2, s2_dim_raster], context)
            self.assertEqual(s2_raster.get_band_names(), \
                             ['masterDs$band_1', 'masterDs$band_2', 'masterDs$band_3', 'masterDs$band_4', 'masterDs$band_5', 'masterDs$band_6',
                              'slaveDs1$band_2', 'slaveDs1$band_4', 'slaveDs2$B2', 'slaveDs2$B4'])