import os
import unittest
import numpy as np

from core.util import expand_var
from core.util.snap import ORBIT_TYPE
from core.raster.funcs import read_band_from_raw
from core.operations import Read, Write, RasterClip
from core.operations.s1 import ApplyOrbit, Calibrate, TopsarDeburst, TerrainCorrection

from core.logic.context import Context


class TestS1Op(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1',
                                              'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')

        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1',
                                             'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')

        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2',
                                         'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

    def do_slc_terrain_correction(self, context):

        read_op = Read(module='snap')
        raster = read_op(self.s1_safe_slc_path, context)
        apply_orbit_op = ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE)
        raster = apply_orbit_op(raster, context)
        calibrate_op = Calibrate(polarisations=['VV'])
        raster = calibrate_op(raster, context)
        deburst_op = TopsarDeburst(polarisations=['VV'])
        raster = deburst_op(raster, context)
        terrain_correction_op = TerrainCorrection()
        raster = terrain_correction_op(raster, context)
        out_path = Write(out_dir=os.path.join(self.data_root, 'target'), out_stem='s1_test', suffix='cal_deburst', out_ext='dim')(raster)

        return out_path

    def test_s1_subset(self):
        context = Context(None)
        out_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/senj/data/test/target/test_out/s1_op/s1_test_cal_deburst.dim'
        out_raster = Read(module='snap')(out_path, context)
        out_raster = RasterClip(bounds=[127.03, 36.39, 127.38, 36.18], copyMetadata=True)(out_raster, context)
        Write(out_dir=os.path.join(self.data_root, 'target', 'test_out','s1_op'), out_stem='s1_test_cal_deburst', suffix='subset', out_ext='dim')(out_raster)

    def do_grdh_terrain_correction(self, context):
        read_op = Read(module='snap')
        raster = read_op(self.s1_safe_grdh_path, context)
        apply_orbit_op = ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE)
        raster = apply_orbit_op(raster, context)
        calibrate_op = Calibrate(polarisations=['VV'])
        raster = calibrate_op(raster, context)
        terrain_correction_op = TerrainCorrection()
        raster = terrain_correction_op(raster, context)
        out_path = Write(out_dir=os.path.join(self.data_root, 'target', 'test_out', 's1_op'), out_stem='grdh',
                         suffix='orb_cal_tc', out_ext='dim')(raster)

        return out_path

    def test_s1_grdh_safe(self):
        context = Context(None)
        # out_path = self.do_grdh_terrain_correction(context)
        out_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/senj/data/test/target/test_out/s1_op/grdh_orb_cal_tc.dim'
        out_raster = Read(module='snap')(out_path, context)
        out_raster = RasterClip(bounds=[128.17124, 35.90668, 128.39547, 35.68248], copyMetadata=True)(out_raster, context)
        Write(out_dir=os.path.join(self.data_root, 'target', 'test_out', 's1_op'), out_stem='s1_grdh_cal_tc',
              suffix='subset', out_ext='dim')(out_raster)