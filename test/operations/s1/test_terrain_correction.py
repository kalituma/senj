import numpy as np
import os
import unittest

from core.config import expand_var
from core.raster import read_gpf_bands_as_dict
from core.util.snap import DemType, InterpolType
from core.operations import Read, Write
from core.operations.s1 import Calibrate, TerrainCorrection
from osgeo import gdal, osr, ogr

from core.logic.context import Context

class TestTerrainCorrection(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1','S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')

    def test_terrain_correction(self):
        context = Context()
        with self.subTest('try to open and terrain correction with different dem name'):
            for dem_type in DemType:
                raster = Read(module='snap')(self.s1_safe_grdh_path, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [25197, 19930])
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=dem_type)(raster, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [34776, 24366])
                self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

    def test_terrain_correction_with_pixel_spacing(self):
        context = Context()
        with self.subTest('try to do terrain correction with different pixel spacing'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [25197, 19930])
            raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, pixelSpacingInMeter=5)(raster, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [34776*2, 24366*2])
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

        with self.subTest('try to do terrain correction with pixel spacing in meter and degree'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [25197, 19930])
            raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, pixelSpacingInMeter=10, pixelSpacingInDegree=0.0008983152)(raster, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [3477, 2436]) # pixelspacing in degree is prior to meter
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

    def test_terrain_correction_with_dem_resampling_method(self):
        context = Context()

        target_dem_inter_type = InterpolType.NEAREST_NEIGHBOUR
        nearest_raster = Read(module='snap')(self.s1_safe_grdh_path, context)
        nearest_raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, pixelSpacingInDegree=0.008983152,
                                           demResamplingMethod=target_dem_inter_type)(nearest_raster, context)
        self.assertEqual([nearest_raster.raw.getSceneRasterWidth(), nearest_raster.raw.getSceneRasterHeight()],[347, 243])
        nearest_dict, _ = read_gpf_bands_as_dict(nearest_raster.raw)

        for i, dem_inter_type in enumerate(InterpolType):
            with self.subTest(f'try to do terrain correction with different resampling method for dem: {dem_inter_type}'):
                if target_dem_inter_type == dem_inter_type:
                    continue

                raster = Read(module='snap')(self.s1_safe_grdh_path, context)
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, pixelSpacingInDegree=0.008983152,
                                           demResamplingMethod=dem_inter_type)(raster, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [347, 243])
                self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

                raster_dict, _ = read_gpf_bands_as_dict(raster.raw)
                self.assertNotEqual(np.sum(raster_dict['Amplitude_VV']['value'] - nearest_dict['Amplitude_VV']['value']), 0)
                self.assertEqual(nearest_dict['Amplitude_VV']['value'].dtype, raster_dict['Amplitude_VV']['value'].dtype)

    def test_terrain_correction_with_img_resampling_method(self):
        context = Context()

        target_dem_inter_type = InterpolType.NEAREST_NEIGHBOUR
        nearest_raster = Read(module='snap')(self.s1_safe_grdh_path, context)
        nearest_raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC,
                                           pixelSpacingInDegree=0.008983152,
                                           demResamplingMethod=target_dem_inter_type,
                                           imgResamplingMethod=target_dem_inter_type)(nearest_raster, context)
        self.assertEqual([nearest_raster.raw.getSceneRasterWidth(), nearest_raster.raw.getSceneRasterHeight()],
                         [347, 243])
        nearest_dict, _ = read_gpf_bands_as_dict(nearest_raster.raw)

        for i, img_inter_type in enumerate(InterpolType):
            with self.subTest(f'try to do terrain correction with different resampling method for dem: {img_inter_type}'):
                if target_dem_inter_type == img_inter_type:
                    continue

                raster = Read(module='snap')(self.s1_safe_grdh_path, context)
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC,
                                           pixelSpacingInDegree=0.008983152,
                                           demResamplingMethod=target_dem_inter_type,
                                           imgResamplingMethod=img_inter_type)(raster, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [347, 243])
                self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

                raster_dict, _ = read_gpf_bands_as_dict(raster.raw)
                self.assertNotEqual(np.sum(raster_dict['Amplitude_VV']['value'] - nearest_dict['Amplitude_VV']['value']), 0)

    def test_terrain_correction_with_dem(self):
        context = Context()
        with self.subTest('try to do terrain correction saving dem'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC,
                                       pixelSpacingInDegree=0.008983152,
                                       demResamplingMethod=InterpolType.BICUBIC_INTERPOLATION,
                                       imgResamplingMethod=InterpolType.BICUBIC_INTERPOLATION,
                                       saveDem=True)(raster, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [347, 243])
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV', 'elevation'])

    def test_terrain_correction_with_map_proj(self):
        utm_raster_path = os.path.join(self.data_root, 'target', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B_TC_bicubic_utm.tif')
        context = Context()
        with self.subTest('try to do terrain correction with different map projection'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC,
                                       pixelSpacingInDegree=0.008983152,
                                       demResamplingMethod=InterpolType.BICUBIC_INTERPOLATION,
                                       imgResamplingMethod=InterpolType.BICUBIC_INTERPOLATION,
                                       mapProjection='epsg:32652')(raster, context)

            utm_raster = Read(module='snap', bands=['Amplitude_VV'])(utm_raster_path, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [utm_raster.raw.getSceneRasterWidth(), utm_raster.raw.getSceneRasterHeight()])
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])
            raster_dict, _ = read_gpf_bands_as_dict(raster.raw)
            utm_dict, _ = read_gpf_bands_as_dict(utm_raster.raw, selected_bands=utm_raster.selected_bands)
            self.assertEqual(np.sum(raster_dict['Amplitude_VV']['value'] - utm_dict['Amplitude_VV']['value']), 0)

    def test_terrain_correction_fail(self):

        context = Context()
        with self.subTest('try to do terrain correction with wrong band name'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(sourceBandNames=['wrong_band_name'], demName=DemType.SRTM_3SEC)(raster, context)

        with self.subTest('try to do terrain correction with wrong dem name'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName='wrong_dem', pixelSpacingInDegree=0.008983152)(raster, context)

        with self.subTest('try to do terrain correction with wrong dem resampling method'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, demResamplingMethod='wrong_interpol')(raster, context)

        with self.subTest('try to do terrain correction with wrong img resampling method'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, imgResamplingMethod='wrong_interpol')(raster, context)

        with self.subTest('try to do terrain correction with wrong projection'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(sourceBandNames=['Amplitude_VV'], demName=DemType.SRTM_3SEC, mapProjection='wrong_projection')(raster, context)

        with self.subTest('do terrain correction with slc product'):
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            with self.assertRaises(RuntimeError):
                raster = TerrainCorrection(sourceBandNames=['i_IW1_VH'], demName=DemType.SRTM_3SEC)(raster, context)