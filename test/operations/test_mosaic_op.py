import os
import unittest
from core.operations import Read, Mosaic, Write
from core.logic import Context
from core.util import expand_var
from core.util.logger import Logger

class TestMosaicOp(unittest.TestCase):

    def setUp(self) -> None:

        self.project_root = expand_var('$PROJECT_PATH/../..')
        self.dir_src_1 = os.path.join(self.project_root, 'INPUTDATA', 'S2', 'dim', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.dir_src_2 = os.path.join(self.project_root, 'INPUTDATA', 'S2', 'dim','subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')

    def test_mosaic_op(self):
        src_1 = os.path.join(self.project_root, 'INPUTDATA', 'S2', 'tif', 'S2A_MSIL1C_20230509T020651.0.tif')
        src_2 = os.path.join(self.project_root, 'INPUTDATA', 'S2', 'tif', 'S2A_MSIL1C_20230509T020651.1.tif')

        out_dir = os.path.join(self.project_root, 'OUTPUTDATA', 'tmp')
        Logger.get_logger(log_file_path=out_dir + 'mosaic_op.log')

        ctx = Context(None)
        src_1_raster = Read(module='snap')(src_1, ctx)
        src_2_raster = Read(module='snap')(src_2, ctx)

        mosaic_raster = Mosaic(master_module='gdal')(rasters=[src_1_raster, src_2_raster], context=ctx)
        Write(out_dir=out_dir, out_stem='mosaic.gdal', out_ext='tif')(mosaic_raster, ctx)

    def test_ps_mosaic_op(self):
        src_1 = os.path.join(self.project_root, 'INPUTDATA', 'PS', '20200817_013159_78_2277_3B.0.tif')
        src_2 = os.path.join(self.project_root, 'INPUTDATA', 'PS', '20200817_013159_99_2277_3B.0.tif')

        out_dir = os.path.join(self.project_root, 'OUTPUTDATA', 'tmp')
        Logger.get_logger(log_file_path=out_dir + 'mosaic_op.log')

        ctx = Context(None)
        src_1_raster = Read(module='gdal')(src_1, ctx)
        src_2_raster = Read(module='gdal')(src_2, ctx)
        mosaic_raster = Mosaic(master_module='gdal')(rasters=[src_1_raster, src_2_raster], context=ctx)