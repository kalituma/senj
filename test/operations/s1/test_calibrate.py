import os
import unittest

from core.raster.gpf_module import ORBIT_TYPE
from core.raster.funcs import read_band_from_raw
from core.operations import Read, Write, Subset
from core.operations.s1 import ApplyOrbit, Calibrate, TopsarDeburst, TerrainCorrection

from core.logic.context import Context

class TestCalibrate(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = '../../resources/data'
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1','S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
