import os
import unittest

from core.config import expand_var

from core.logic.context import Context
from core.operations import Read, Write, Split, MultiWrite

class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = expand_var('$PROJECT_PATH')
        self.s2_target_path = os.path.join(self.project_path, 'data', 'test', 'target')

        self.s2_safe_path = os.path.join(self.project_path, 'data', 'test', 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')

        self.atmos_user_conf = os.path.join(self.project_path, 'test', 'resources', 'config', 'atmos', 'S2A_MSI.txt')

    def test_read_and_multi_write(self):
        out_path = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'safe_splitted', 'out.tif')
        # s2_raster = Read(module='snap')(self.s2_safe_path, Context())
        s2_dim_raster = Read(module='snap')(self.s2_safe_path, Context())

        s2_raster_list = Split(bands=[['B2', 'B3', 'B4'],
                                      ['B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4']])(s2_dim_raster, Context())

        out_paths = MultiWrite(out_path, module='snap')(s2_raster_list, Context())

    def test_read_det_gdal(self):
        tif_path = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'splitted_multi_band',
                                'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')

        out_path = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'splitted_multi_band_gdal', 'out.tif')

        raster = Read(module='gdal')(tif_path, Context())
        s2_dim_raster_list = Split(bands=[[1, 2], [3]])(raster, Context())
        out_paths = MultiWrite(out_path, module='gdal', out_ext='tif')(s2_dim_raster_list, Context())