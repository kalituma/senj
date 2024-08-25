import os, unittest

from core.logic import Context
from core.config import expand_var
from core.operations import Read, Subset, Write
class TestSubset(unittest.TestCase):
    def setUp(self) -> None:
        self.test_data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_safe_path = os.path.join(self.test_data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_snap_tif = os.path.join(self.test_data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')

    def test_subset(self):
        out_path = os.path.join(self.test_data_root, 'subset.tif')
        context = Context()
        snap_tif_raster = Read(module='snap')(self.s2_snap_tif, context)
        snap_tif_raster = Subset(bounds=[128.252, 34.9448, 128.3277, 34.8775], bands=['B1', 'B3', 'B4'])(snap_tif_raster, context)
        print(Write(module='snap', path=out_path)(snap_tif_raster, context))


