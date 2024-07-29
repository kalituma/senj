import os
import unittest

from core.config import expand_var

from core.logic.context import Context
from core.operations import Read, Write, Split, MultiWrite

class TestSplitOp(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_without_meta = os.path.join(self.data_root, 's2merge_1_stack_subset.tif')

        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap',
                                        'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')


    def test_split_without_metadict(self):
        out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta', 'split_without_meta.tif')
        context = Context()
        result_raster = Read(module='snap')(self.s2_without_meta, context)
        result_raster = Split(bands=[['band_1', 'band_2'], ['band_4', 'band_5']])(result_raster, context)
        MultiWrite(out_path, module='snap')(result_raster, context)
        print()

    def test_split_without_metadict_index(self):
        out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_index', 'split_without_meta.tif')
        context = Context()
        result_raster = Read(module='snap')(self.s2_without_meta, context)
        result_raster = Split(bands=[[1, 2], [4, 5]])(result_raster, context)
        MultiWrite(out_path, module='snap')(result_raster, context)
        print()

    def test_split_gdal_without_metadict(self):
        out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_gdal', 'split_without_meta.tif')
        context = Context()
        result_raster = Read(module='gdal')(self.s2_without_meta, context)
        result_raster = Split(bands=[['band_1', 'band_2'], ['band_4', 'band_5']])(result_raster, context)
        MultiWrite(out_path, module='gdal')(result_raster, context)
        print()