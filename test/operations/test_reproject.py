import os
import unittest
from esa_snappy import Product

from core.operations import Read, Reproject, Write
from core.logic import Context
from core.config import expand_var

class TestReproject(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_dim_path = os.path.join(self.test_data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')

    def test_reproject(self):
        out_path = os.path.join(self.test_data_root, 'reproject.tif')
        context = Context(None)
        with self.subTest(msg='reproject'):
            snap_raster = Read(module='snap')(self.s1_dim_path, context)
            snap_raster = Reproject(epsg=4326, resampling_method='nearest', pixel_size=0.0002)(snap_raster, None)
            out_path = Write(out_dir=self.test_data_root, out_stem='reproject_out_00002', out_ext='tif')(snap_raster, context)
            self.assertTrue(os.path.exists(out_path))