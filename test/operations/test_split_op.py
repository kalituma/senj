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
        self.s2_safe = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')


    def test_split_without_metadict(self):

        context = Context()
        with self.subTest('Split without meta using SNAP'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta', 'split_without_meta.tif')
            result_raster = Read(module='snap')(self.s2_without_meta, context)
            result_raster = Split(bands=[['band_1', 'band_2'], ['band_4', 'band_5']])(result_raster, context)
            MultiWrite(out_path, module='snap')(result_raster, context)

        with self.subTest('Split without meta using SNAP'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_gdal', 'split_without_meta_gdal.tif')
            result_raster = Read(module='gdal')(self.s2_without_meta, context)
            result_raster = Split(bands=[['band_1', 'band_2'], ['band_4', 'band_5']])(result_raster, context)
            MultiWrite(out_path, module='gdal')(result_raster, context)

        with self.subTest('Split without meta using SNAP/GDAL'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_snap_gdal', 'split_without_meta_snap_gdal.tif')
            result_raster = Read(module='snap')(self.s2_without_meta, context)
            result_raster = Split(bands=[['band_1', 'band_2'], ['band_4', 'band_5']])(result_raster, context)
            MultiWrite(out_path, module='gdal')(result_raster, context)

        with self.subTest('Split without meta using GDAL/GDAL'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_gdal_snap', 'split_without_meta_gdal_snap.tif')
            result_raster = Read(module='gdal')(self.s2_without_meta, context)
            result_raster = Split(bands=[['band_1', 'band_2'], ['band_4', 'band_5']])(result_raster, context)
            MultiWrite(out_path, module='snap')(result_raster, context)

    def test_split_without_metadict_using_index(self):

        context = Context()
        with self.subTest('Split with index using SNAP'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_index', 'split_without_meta_index.tif')
            result_raster = Read(module='snap')(self.s2_without_meta, context)
            result_raster = Split(bands=[[1, 2], [3, 4]])(result_raster, context)
            MultiWrite(out_path, module='snap')(result_raster, context)

        with self.subTest('Split with index using SNAP/GDAL'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_index_snap_gdal', 'split_without_meta_index_snap_gdal.tif')
            result_raster = Read(module='snap')(self.s2_without_meta, context)
            result_raster = Split(bands=[[1, 2], [3, 4]])(result_raster, context)
            MultiWrite(out_path, module='gdal')(result_raster, context)

        with self.subTest('Split with index using GDAL'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_index_gdal_gdal', 'split_without_meta_index_gdal_gdal.tif')
            result_raster = Read(module='gdal')(self.s2_without_meta, context)
            result_raster = Split(bands=[[1, 2], [3, 4]])(result_raster, context)
            MultiWrite(out_path, module='gdal')(result_raster, context)

        with self.subTest('Split with index using GDAL/SNAP'):
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_without_meta_index_gdal_snap', 'split_without_meta_index_gdal_snap.tif')
            result_raster = Read(module='gdal')(self.s2_without_meta, context)
            result_raster = Split(bands=[[1, 2], [3, 4]])(result_raster, context)
            MultiWrite(out_path, module='snap')(result_raster, context)

    def test_split_dim(self):
        context = Context()
        out_path = os.path.join(self.data_root, 'target', 's2', 'split_dim', 'split_dim.tif')
        dim_raster = Read(module='snap')(self.s2_dim_path, context)
        rasters = Split(bands=[['B2', 'B3', 'B4'],
                               ['B2', 'B3', 'B4'],
                               ['B2', 'B3', 'B4']])(dim_raster, context)
        MultiWrite(out_path, module='snap')(rasters, context)

    def test_split_with_meta_tif_snap(self):
        with self.subTest('Split with meta using SNAP'):
            context = Context()
            out_path = os.path.join(self.data_root, 'tif', 's2', 'snap', 'out.tif')

            # out_path = os.path.join(self.data_root, 'target', 's2', 'split_with_meta', 'split_with_meta.tif')

            result_raster = Read(module='snap')(self.s2_dim_path, context)
            # Write(out_path, module='snap')(result_raster, context)

            result_raster = Split(bands=[['B2', 'B3', 'B4',
                                          'B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4'],
                                         ['B2', 'B3', 'B4',
                                          'B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4'],
                                         ['B2', 'B3', 'B4',
                                          'B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4']])(result_raster, context)
            MultiWrite(out_path, module='snap')(result_raster, context)

    def test_split_with_meta_tif_gdal(self):

        with self.subTest('Split with meta using GDAL and index'):
            context = Context()
            in_path = os.path.join(self.data_root, 'tif', 's2', 'gdal', 'out_0_read.tif')
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_gdal', 'split_gdal.tif')
            result_raster = Read(module='gdal')(in_path, context)
            result_rasters = Split(bands=[[1, 2, 3], [4, 5, 6]])(result_raster, context)
            MultiWrite(out_path, module='gdal')(result_rasters, context)

        with self.subTest('Split with meta using GDAL and name'):
            context = Context()
            in_path = os.path.join(self.data_root, 'tif', 's2', 'gdal', 'out_0_read.tif')
            out_path = os.path.join(self.data_root, 'target', 's2', 'split_gdal_index', 'split_gdal_index.tif')
            result_raster = Read(module='gdal')(in_path, context)
            result_rasters = Split(bands=[['B2', 'B3', 'B4'],
                                          ['B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4']])(result_raster, context)
            MultiWrite(out_path, module='gdal')(result_rasters, context)

    def test_split_safe(self):
        context = Context()
        out_path = os.path.join(self.data_root, 'target', 's2', 'split_safe', 'split_safe.tif')
        safe_raster = Read(module='snap')(self.s2_safe, context)
        rasters = Split(bands=[['B1', 'B_detector_footprint_B1'],
                               ['B2', 'B_detector_footprint_B2'],
                               ['B6', 'B_detector_footprint_B6']
                               ])(safe_raster, context)
        MultiWrite(out_path, module='snap')(rasters, context)
