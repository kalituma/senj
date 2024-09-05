import numpy as np
import os
import unittest

from core.util import expand_var
from core.util.errors import ModuleError, ProductTypeError
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
        self.s1_tif = self.s1_tif_snap_path = os.path.join(self.data_root, 'tif', 's1', 'snap', 'src_1', 'terrain_corrected_0.tif')
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
    def test_terrain_correction(self):
        context = Context(None)
        with self.subTest('try to open and terrain correction with different dem name'):
            for dem_type in DemType:
                raster = Read(module='snap')(self.s1_safe_grdh_path, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [25197, 19930])
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=dem_type)(raster, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [34776, 24366])
                self.assertEqual(raster.get_band_names(), ['Amplitude_VV'])

    def test_terrain_correction_with_pixel_spacing(self):
        context = Context(None)
        with self.subTest('try to do terrain correction with different pixel spacing'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [25197, 19930])
            raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, pixel_spacing_meter=5)(raster, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [34776*2, 24366*2])
            self.assertEqual(raster.get_band_names(), ['Amplitude_VV'])

        with self.subTest('try to do terrain correction with pixel spacing in meter and degree'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [25197, 19930])
            raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, pixel_spacing_meter=10, pixel_spacing_degree=0.0008983152)(raster, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [3477, 2436]) # pixelspacing in degree is prior to meter
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

    def test_terrain_correction_with_dem_resampling_method(self):
        context = Context(None)

        target_dem_inter_type = InterpolType.NEAREST_NEIGHBOUR
        nearest_raster = Read(module='snap')(self.s1_safe_grdh_path, context)
        nearest_raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, pixel_spacing_degree=0.008983152,
                                           dem_method=target_dem_inter_type)(nearest_raster, context)
        self.assertEqual([nearest_raster.raw.getSceneRasterWidth(), nearest_raster.raw.getSceneRasterHeight()],[347, 243])
        nearest_dict, _ = read_gpf_bands_as_dict(nearest_raster.raw)

        for i, dem_inter_type in enumerate(InterpolType):
            with self.subTest(f'try to do terrain correction with different resampling method for dem: {dem_inter_type}'):
                if target_dem_inter_type == dem_inter_type:
                    continue

                raster = Read(module='snap')(self.s1_safe_grdh_path, context)
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, pixel_spacing_degree=0.008983152,
                                           dem_method=dem_inter_type)(raster, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [347, 243])
                self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

                raster_dict, _ = read_gpf_bands_as_dict(raster.raw)
                self.assertNotEqual(np.sum(raster_dict['Amplitude_VV']['value'] - nearest_dict['Amplitude_VV']['value']), 0)
                self.assertEqual(nearest_dict['Amplitude_VV']['value'].dtype, raster_dict['Amplitude_VV']['value'].dtype)

    def test_terrain_correction_with_img_resampling_method(self):
        context = Context(None)

        target_dem_inter_type = InterpolType.NEAREST_NEIGHBOUR
        nearest_raster = Read(module='snap')(self.s1_safe_grdh_path, context)
        nearest_raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC,
                                           pixel_spacing_degree=0.008983152,
                                           dem_method=target_dem_inter_type,
                                           img_method=target_dem_inter_type)(nearest_raster, context)
        self.assertEqual([nearest_raster.raw.getSceneRasterWidth(), nearest_raster.raw.getSceneRasterHeight()],
                         [347, 243])
        nearest_dict, _ = read_gpf_bands_as_dict(nearest_raster.raw)

        for i, img_inter_type in enumerate(InterpolType):
            with self.subTest(f'try to do terrain correction with different resampling method for dem: {img_inter_type}'):
                if target_dem_inter_type == img_inter_type:
                    continue

                raster = Read(module='snap')(self.s1_safe_grdh_path, context)
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC,
                                           pixel_spacing_degree=0.008983152,
                                           dem_method=target_dem_inter_type,
                                           img_method=img_inter_type)(raster, context)
                self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [347, 243])
                self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])

                raster_dict, _ = read_gpf_bands_as_dict(raster.raw)
                self.assertNotEqual(np.sum(raster_dict['Amplitude_VV']['value'] - nearest_dict['Amplitude_VV']['value']), 0)

    def test_terrain_correction_with_dem(self):
        context = Context(None)
        with self.subTest('try to do terrain correction saving dem'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC,
                                       pixel_spacing_degree=0.008983152,
                                       dem_method=InterpolType.BICUBIC_INTERPOLATION,
                                       img_method=InterpolType.BICUBIC_INTERPOLATION,
                                       save_dem=True)(raster, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [347, 243])
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV', 'elevation'])

    def test_terrain_correction_with_map_proj(self):
        utm_raster_path = os.path.join(self.data_root, 'target', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B_TC_bicubic_utm.tif')
        context = Context(None)
        with self.subTest('try to do terrain correction with different map projection'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC,
                                       pixel_spacing_degree=0.008983152,
                                       dem_method=InterpolType.BICUBIC_INTERPOLATION,
                                       img_method=InterpolType.BICUBIC_INTERPOLATION,
                                       map_projection='epsg:32652')(raster, context)

            utm_raster = Read(module='snap', bands=['Amplitude_VV'])(utm_raster_path, context)
            self.assertEqual([raster.raw.getSceneRasterWidth(), raster.raw.getSceneRasterHeight()], [utm_raster.raw.getSceneRasterWidth(), utm_raster.raw.getSceneRasterHeight()])
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV'])
            raster_dict, _ = read_gpf_bands_as_dict(raster.raw)
            utm_dict, _ = read_gpf_bands_as_dict(utm_raster.raw, selected_bands=utm_raster.selected_bands)
            self.assertEqual(np.sum(raster_dict['Amplitude_VV']['value'] - utm_dict['Amplitude_VV']['value']), 0)

    def test_terrain_correction_with_wrong_params(self):

        context = Context(None)
        with self.subTest('try to do terrain correction with wrong band name'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(bands=['wrong_band_name'], dem_name=DemType.SRTM_3SEC)(raster, context)

        with self.subTest('try to do terrain correction with wrong dem name'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name='wrong_dem', pixel_spacing_degree=0.008983152)(raster, context)

        with self.subTest('try to do terrain correction with wrong dem resampling method'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, dem_method='wrong_interpol')(raster, context)

        with self.subTest('try to do terrain correction with wrong img resampling method'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, img_method='wrong_interpol')(raster, context)

        with self.subTest('try to do terrain correction with wrong projection'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context)
            with self.assertRaises(AssertionError):
                raster = TerrainCorrection(bands=['Amplitude_VV'], dem_name=DemType.SRTM_3SEC, map_projection='wrong_projection')(raster, context)

        with self.subTest('do terrain correction with slc product'): # if slc product should be able to be corrected, topsar deburst should be done first
            raster = Read(module='snap')(self.s1_safe_slc_path, context)
            with self.assertRaises(RuntimeError):
                raster = TerrainCorrection(bands=['i_IW1_VH'], dem_name=DemType.SRTM_3SEC)(raster, context)

    def test_terrain_correction_fail(self):
        context = Context(None)
        with self.subTest('do terrain correction with the file format in wrong module'):
            raster = Read(module='gdal')(self.s1_tif, context)
            with self.assertRaises(ModuleError):
                raster = TerrainCorrection(dem_name=DemType.SRTM_3SEC)(raster, context)

        with self.subTest('do terrain correction with already corrected file'):
            raster = Read(module='snap')(self.s1_tif, context)
            with self.assertRaises(RuntimeError):
                raster = TerrainCorrection(dem_name=DemType.SRTM_3SEC)(raster, context)

        with self.subTest('do terrain correction with the file format in wrong product type'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(ProductTypeError):
                raster = TerrainCorrection(dem_name=DemType.SRTM_3SEC)(raster, context)