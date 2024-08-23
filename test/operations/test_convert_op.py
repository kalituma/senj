import os, unittest
from core.config import expand_var

class TestConverOp(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_tif_snap_path = os.path.join(self.data_root, 'tif', 's1', 'snap', 'src_1', 'terrain_corrected_0.tif')

    def test_convert_op(self):
        from core.operations import Read, Convert
        from core.logic.context import Context

        s1_raster = Read(module='snap')(self.s1_dim_path, Context())
        s2_raster = Read(module='snap')(self.s2_dim_path, Context())

        s1_raster = Convert()(s1_raster, Context())
        s2_raster = Convert()(s2_raster, Context())

        print()