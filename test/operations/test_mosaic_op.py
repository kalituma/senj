import unittest
from core.operations import Read, Mosaic, Write
from core.logic import Context
from core.util.logger import Logger

class TestMosaicOp(unittest.TestCase):

    def setUp(self) -> None:
        self.src_1 = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/tif/S2A_MSIL1C_20230509T020651.0.tif'
        self.src_2 = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/tif/S2A_MSIL1C_20230509T020651.1.tif'
        self.out_dir = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_example/INPUTDATA/S2/tif/'
        Logger.get_logger(log_file_path=self.out_dir + 'mosaic_op.log')

    def test_mosaic_op(self):
        ctx = Context(None)
        src_1_raster = Read(module='gdal')(self.src_1, ctx)
        src_2_raster = Read(module='snap')(self.src_2, ctx)

        mosaic_raster = Mosaic(master_module='snap')(rasters=[src_1_raster, src_2_raster], context=ctx)
        Write(out_dir=self.out_dir, out_stem='mosaic.snap', out_ext='tif')(mosaic_raster, ctx)