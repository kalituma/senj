import os, unittest

from core.logic import Context
from core.config import expand_var
from core.operations import Write, Read, Select
from core.raster.funcs import read_band_from_raw

class TestReadWriteGlobal(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.out_dir = os.path.join(self.data_root, 'target', 'test_out', 'no_meta_with_tif_head')
        self.no_meta_path = os.path.join(self.data_root, 'tif', 'no_meta', 'out_0_read.tif')

    def test_read_write_with_no_meta_gdal(self):
        context = Context(None)

        partial_no_meta = Read(module='snap', bands=[4,5])(self.no_meta_path, context)
        out_path = Write(out_dir=self.out_dir, out_stem='read_write_with_band_option', out_ext='tif')(partial_no_meta, context)
        out_raster = Read(module='gdal')(out_path, context)
        self.assertEqual(out_raster.get_band_names(), ['band_4', 'band_5'])

        no_meta = Read(module='snap')(self.no_meta_path, context)
        no_meta_sel = Select(bands=['band_2', 'band_4'])(no_meta, context)
        out_path = Write(out_dir=self.out_dir, out_stem='read_select_write', out_ext='tif')(no_meta_sel, context)

        out_raster = Read(module='gdal')(out_path, context)
        self.assertEqual(out_raster.get_band_names(), ['band_2', 'band_4'])
