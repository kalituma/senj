import os
import unittest
import numpy as np

from core.raster.gpf_module import ORBIT_TYPE
from core.util import ProductTypeError
from core.util.errors import ModuleError
from core.operations import Read, Write, Subset
from core.operations.s1 import ApplyOrbit, Calibrate, TopsarDeburst, TerrainCorrection

from core.logic.context import Context

class TestApplyOrbit(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = '../../resources/data'
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1','S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_grdh_subset_target = os.path.join(self.data_root, 'target', 'subset_4_of_S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B_Orb_Cal_TC.dim')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s1_grdh_tif = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')

    def test_apply_orbit(self):
        context = Context()
        with self.subTest('try to open and apply orbit'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            prev_orbit = raster.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'].copy()
            raster = ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE)(raster, context)
            cur_orbit = raster.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'].copy()
            self.assertNotEqual(prev_orbit, cur_orbit)
            raster = ApplyOrbit(orbitType=ORBIT_TYPE.K5_PRECISE, continueOnFail=False)(raster, context)
            k5_orbit = raster.meta_dict['Abstracted_Metadata']['Orbit_State_Vectors'].copy()
            self.assertEqual(cur_orbit, k5_orbit)

    def test_apply_orbit_polydegree(self):
        context = Context()
        raster_1 = Read(module='snap')(self.s1_safe_grdh_path, context)
        raster_poly_3 = ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE, polyDegree=3, continueOnFail=False)(raster_1, context)

        raster_2 = Read(module='snap')(self.s1_safe_grdh_path, context)
        raster_poly_6 = ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE, polyDegree=6, continueOnFail=False)(raster_2,context)

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
        context = Context()

        with self.subTest('try to apply orbit to non-s1 raster'):
            s2_raster = Read(module='snap')(self.s2_safe_path, context)
            with self.assertRaises(ProductTypeError):
                ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE, continueOnFail=False)(s2_raster, context)

        with self.subTest('try to apply orbit with wrong orbit type'):
            s1_raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(RuntimeError):
                ApplyOrbit(orbitType='wrong_orbit_type', continueOnFail=False)(s1_raster, context)

        with self.subTest('try to apply orbit to tif raster'):
            s2_raster = Read(module='gdal')(self.s1_grdh_tif, context)
            with self.assertRaises(ModuleError):
                ApplyOrbit(orbitType=ORBIT_TYPE.SENTINEL_PRECISE, continueOnFail=False)(s2_raster, context)
