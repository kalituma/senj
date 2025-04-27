import os
import unittest
import numpy as np

from core.util import expand_var
from core.util.snap import ORBIT_TYPE
from core.util.errors import ModuleError, ProductTypeError, ExtensionError
from core.operations import Read, Write, RasterClip
from core.operations.s1 import ApplyOrbit, Calibrate, TopsarDeburst, TerrainCorrection

from core.logic.context import Context

class TestApplyOrbit(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1','S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_grdh_subset_target = os.path.join(self.data_root, 'target', 'subset_4_of_S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B_Orb_Cal_TC.dim')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s1_grdh_tif = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')

    def test_apply_orbit(self):

        context = Context(None)
        with self.subTest('try to open and apply orbit'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            prev_orbit = raster.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'].copy()
            raster = ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE)(raster, context)
            cur_orbit = raster.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'].copy()
            self.assertNotEqual(prev_orbit, cur_orbit)
            raster = ApplyOrbit(orbit_type=ORBIT_TYPE.K5_PRECISE, continue_on_fail=False)(raster, context)
            k5_orbit = raster.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'].copy()
            self.assertEqual(cur_orbit, k5_orbit)

    def test_apply_orbit_polydegree(self):
        context = Context(None)
        raster_1 = Read(module='snap')(self.s1_safe_grdh_path, context)
        raster_poly_3 = ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE, poly_degree=3, continue_on_fail=False)(raster_1, context)

        raster_2 = Read(module='snap')(self.s1_safe_grdh_path, context)
        raster_poly_6 = ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE, poly_degree=6, continue_on_fail=False)(raster_2, context)

        for i in range(1, 5):
            with self.subTest():
                self.assertNotEqual(
                    float(raster_poly_3.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['x_pos']) - \
                    float(raster_poly_6.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['x_pos']), 0)

                self.assertNotEqual(
                    float(raster_poly_3.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['y_pos'])- \
                    float(raster_poly_6.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['y_pos']), 0)
                self.assertNotEqual(
                    float(raster_poly_3.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['z_pos']) - \
                    float(raster_poly_6.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['z_pos']), 0)
                self.assertNotEqual(
                    float(raster_poly_3.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['x_vel']) - \
                    float(raster_poly_6.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['x_vel']), 0)
                self.assertNotEqual(
                    float(raster_poly_3.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['y_vel']) - \
                    float(raster_poly_6.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['y_vel']), 0)
                self.assertNotEqual(
                    float(raster_poly_3.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['z_vel']) - \
                    float(raster_poly_6.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'][f'orbit_vector{i}']['z_vel']), 0)

    def testApplyOrbitFail(self):
        context = Context(None)

        with self.subTest('try to apply orbit to non-s1 raster'):
            s2_raster = Read(module='snap')(self.s2_safe_path, context)
            with self.assertRaises(ProductTypeError):
                ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE, continue_on_fail=False)(s2_raster, context)

        with self.subTest('try to apply orbit with wrong orbit type'):
            s1_raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(RuntimeError):
                ApplyOrbit(orbit_type='wrong_orbit_type', continue_on_fail=False)(s1_raster, context)

        with self.subTest('try to apply orbit to tif raster'):
            s2_raster = Read(module='gdal')(self.s1_grdh_tif, context)
            with self.assertRaises(ModuleError):
                ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE, continue_on_fail=False)(s2_raster, context)

        with self.subTest('try to apply orbit with the file which has wrong extension'):
            s2_raster = Read(module='snap')(self.s1_grdh_tif, context)
            with self.assertRaises(ExtensionError):
                ApplyOrbit(orbit_type=ORBIT_TYPE.SENTINEL_PRECISE, continue_on_fail=False)(s2_raster, context)