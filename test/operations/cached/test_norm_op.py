import os, unittest
from core.logic import Context
from core.util import expand_var, Logger
from core.operations import Read, Write
from core.operations.etri import Normalize

class TestNormOP(unittest.TestCase):
    def test_normalize(self):
        in_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/_product/etri_example_updated/OUTPUTDATA/WildFireDamageArea_Preprocessing/S2A_MSIL1C_20230412T021531_N0509_R003_T52SBF_20230412T043905.SAFE_stack_coo_subset_resample.tif'
        ctx = Context(None)
        in_raster = Read(module='gdal')(in_path, ctx)
        out_raster = Normalize(method='minmax',min=0,max=255)(in_raster, ctx)
        print()