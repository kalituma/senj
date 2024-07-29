import os
import unittest
from core.raster.funcs import  update_meta_band_map
from core.config import expand_var
from core.logic.context import Context
from core.operations import Read, Write, Split, MultiWrite

class TestRasterBandNameAndIndices(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_without_meta = os.path.join(self.data_root, 's2merge_1_stack_subset.tif')
        self.s2_dim = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s2_tif = os.path.join(self.data_root, 'tif', 's2', 'snap', 'out.tif')

    def test_read_and_band_map(self):
        context = Context()
        with self.subTest('read tif not having meta using snap'):
            result_raster = Read(module='snap')(self.s2_without_meta, context)
            self.assertEqual(result_raster.get_band_names(), [f'band_{index}' for index in range(1, len(result_raster.raw.getBands()) + 1)])

        with self.subTest('read dim file'):
            result_raster = Read(module='snap')(self.s2_dim, context)
            self.assertEqual(result_raster.get_band_names(), list(result_raster._index_to_band.values()))
            meta_dict = result_raster.meta_dict
            new_meta = update_meta_band_map(meta_dict, [1, 2, 3])
            result_raster.meta_dict = new_meta
            self.assertEqual(result_raster._index_to_band, new_meta['index_to_band'])



    # def test_multi_write(self):
    #
    #     s2_raster = Read(module='snap')(self.s2_dim, Context())
    #     s2_raster_list = Split(bands=[['B2', 'B3', 'B4', 'B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4']])(s2_raster, Context())
    #     out_paths = MultiWrite(out_path, module='snap')(s2_raster_list, Context())