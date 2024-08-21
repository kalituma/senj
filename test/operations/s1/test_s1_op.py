import os
import unittest
import numpy as np

from core.config import expand_var
from core.util.snap import ORBIT_TYPE
from core.raster.funcs import read_band_from_raw
from core.operations import Read, Write, Subset
from core.operations.s1 import ApplyOrbit, Calibrate, TopsarDeburst, TerrainCorrection

from core.logic.context import Context


class TestS1Op(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', '',
                                              'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_grdh_subset_target = os.path.join(self.data_root, 'target', 'subset_4_of_S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B_Orb_Cal_TC.dim')

        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', '',
                                             'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s1_slc_subset_target = os.path.join(self.data_root, 'target','subset_1_of_S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061_Orb_Cal_deb_TC.dim')

        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2',
                                         'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

    def test_s1_slc_safe(self):
        context = Context()
        read_op = Read(module='snap')
        raster = read_op(self.s1_safe_slc_path, context)
        apply_orbit_op = ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE)
        raster = apply_orbit_op(raster, context)
        calibrate_op = Calibrate(selectedPolarisations=['VV'])
        raster = calibrate_op(raster, context)
        deburst_op = TopsarDeburst(selectedPolarisations=['VV'])
        raster = deburst_op(raster, context)
        terrain_correction_op = TerrainCorrection()
        raster = terrain_correction_op(raster, context)
        out_path = Write(path=os.path.join(self.data_root, 'target'), module='snap', suffix='cal_deburst', out_ext='dim')(raster)

        out_raster = Read(module='snap')(out_path, context)
        out_raster = Subset(bbox=[7500, 7500, 2501, 2501], copyMetadata=True)(out_raster, context)
        cached_result = read_band_from_raw(raster=out_raster, selected_band=['Sigma0_VV'])

        target_raster = Read(module='snap')(self.s1_slc_subset_target, context)
        cached_target = read_band_from_raw(raster=target_raster, selected_band=['Sigma0_VV'])

        self.assertEqual(np.sum(cached_result.bands['Sigma0_VV']['value'] - cached_target.bands['Sigma0_VV']['value']), 0)

    def test_s1_grdh_safe(self):
        context = Context()
        read_op = Read(module='snap')
        raster = read_op(self.s1_safe_grdh_path, context)
        apply_orbit_op = ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE)
        raster = apply_orbit_op(raster, context)
        calibrate_op = Calibrate(selectedPolarisations=['VV'])
        raster = calibrate_op(raster, context)
        terrain_correction_op = TerrainCorrection()
        raster = terrain_correction_op(raster, context)
        out_path = Write(path=os.path.join(self.data_root, 'target'), module='snap', suffix='orb_cal_tc', out_ext='dim')(raster)
        out_raster = Read(module='snap')(out_path, context)
        out_raster = Subset(bounds=[128.17124, 35.90668, 128.39547, 35.68248], copyMetadata=True)(out_raster, context)
        cached_result = read_band_from_raw(raster=out_raster, selected_band=['Sigma0_VV'])

        target_raster = Read(module='snap')(self.s1_grdh_subset_target, context)
        cached_target = read_band_from_raw(raster=target_raster, selected_band=['Sigma0_VV'])

        self.assertEqual(np.sum(cached_result.bands['Sigma0_VV']['value'][:-1, :-1] - cached_target.bands['Sigma0_VV']['value']),0)