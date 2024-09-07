import os
import numpy as np
import unittest

from core.raster.funcs import get_res, get_epsg
from core.operations import Read, Resample, Write
from core.logic import Context
from core.util import expand_var

class TestReproject(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_dim_path = os.path.join(self.test_data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s1_tif_path = os.path.join(self.test_data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')

    def test_reproject_snap(self):
        context = Context(None)
        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'reproejct_op')
        with self.subTest(msg='reproject using snap'):
            read_op = Read(module='snap')
            snap_raster = read_op(self.s1_tif_path, context)
            resample_op = Resample(epsg=5186, pixel_size=11.277, resampling_method='bicubic')
            resample_op.module_type = 'snap'
            snap_raster = resample_op(snap_raster, None)
            Write(out_dir=out_dir, out_stem='reproject_snap', out_ext='tif')(snap_raster, context)
            self.assertEqual(get_epsg(snap_raster), 5186)
            self.assertTrue(np.isclose(get_res(snap_raster), 11.277))

        with self.subTest(msg='reproject using snap'):
            read_op = Read(module='snap')
            snap_raster = read_op(self.s1_tif_path, context)
            resample_op = Resample(resampling_method='nearest', pixel_size=0.0002)
            resample_op.module_type = 'snap'
            snap_raster = resample_op(snap_raster, None)
            Write(out_dir=out_dir, out_stem='resample_snap', out_ext='tif')(snap_raster, context)
            self.assertEqual(get_epsg(snap_raster), 4326)
            self.assertTrue(np.isclose(get_res(snap_raster), 0.0002))
    def test_resample(self):
        context = Context(None)
        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'reproejct_op')
        with self.subTest(msg='reproject using snap'):
            read_op = Read(module='snap')
            snap_raster = read_op(self.s1_tif_path, context)
            resample_op = Resample(pixel_size=0.00008, resampling_method='bicubic')
            resample_op.module_type = 'snap'
            snap_raster = resample_op(snap_raster, None)
            Write(out_dir=out_dir, out_stem='resample_snap', out_ext='tif')(snap_raster, context)
            self.assertEqual(get_epsg(snap_raster), 4326)
            self.assertTrue(np.isclose(get_res(snap_raster), 0.00008))

    def test_reproject_gdal(self):
        context = Context(None)
        out_dir = os.path.join(self.test_data_root, 'target', 'test_out', 'reproejct_op')
        with self.subTest(msg='reproject using gdal'):
            read_op = Read(module='gdal')
            gdal_raster = read_op(self.s1_tif_path, context)
            resample_op = Resample(epsg=5186, resampling_method='bicubic')
            resample_op.module_type = 'gdal'
            gdal_raster = resample_op(gdal_raster, None)
            # Write(out_dir=out_dir, out_stem='reproject_gdal', out_ext='tif')(gdal_raster, context)
            self.assertEqual(get_epsg(gdal_raster), 5186)
            self.assertTrue(np.isclose(get_res(gdal_raster), 12.63932652576442))

        with self.subTest(msg='reproject using gdal'):
            read_op = Read(module='gdal')
            gdal_raster = read_op(self.s1_tif_path, context)
            resample_op = Resample(resampling_method='cubicspline', pixel_size=0.0002)
            resample_op.module_type = 'gdal'
            gdal_raster = resample_op(gdal_raster, None)
            Write(out_dir=out_dir, out_stem='resample_gdal', out_ext='tif')(gdal_raster, context)
            self.assertEqual(get_epsg(gdal_raster), 4326)
            self.assertTrue(np.isclose(get_res(gdal_raster), 0.0002))

