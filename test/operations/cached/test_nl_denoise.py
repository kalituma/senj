import os, unittest
import numpy as np
from core.logic import Context
from core.util import expand_var
from core.raster.funcs import read_band_from_raw
from core.operations import Read, Write
from core.operations.cached import NLMeanDenoising

class TestMeanDenoising(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_tif_path = os.path.join(self.data_root, 'tif', 's2', 'snap',
                                        'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')

        self.wv_xml_path = os.path.join(self.data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS-014493935010_01_P001.XML')
        self.ps_xml_path = os.path.join(self.data_root, 'tif', 'ps', '20190817_Radiance', 'files',
                                        '20200817_013159_78_2277_3B_AnalyticMS_metadata_clip.xml')
    def test_mean_denoising_to_s2_dim(self):
        context = Context(None)
        with self.subTest('SNAP and GDAL with s2 product'):
            raster_snap = Read(module='snap', bands=[1,2,3])(self.s2_tif_path, context)
            raster_snap = NLMeanDenoising(bands=[1])(raster_snap, context)
            raster_snap = read_band_from_raw(raster_snap, selected_name_or_id=[1])

            raster_gdal = Read(module='gdal', bands=[1,2,3])(self.s2_tif_path, context)
            raster_gdal = NLMeanDenoising(bands=[1])(raster_gdal, context)
            raster_gdal = read_band_from_raw(raster_gdal, selected_name_or_id=['B2'])

            self.assertEqual(np.sum(raster_gdal['B2']['value']), np.sum(raster_snap['B2']['value']))


        with self.subTest('SNAP and GDAL with wv product'):
            raster_snap = Read(module='snap', bands=['BAND_G'])(self.wv_xml_path, context)
            raster_snap = NLMeanDenoising(bands=[1])(raster_snap, context)
            raster_snap = read_band_from_raw(raster_snap, selected_name_or_id=['BAND_G'])

            raster_gdal = Read(module='gdal', bands=['BAND_R', 'BAND_G', 'BAND_B'])(self.wv_xml_path, context)
            raster_gdal = NLMeanDenoising()(raster_gdal, context)
            raster_gdal = read_band_from_raw(raster_gdal, selected_name_or_id=['BAND_R', 'BAND_G', 'BAND_B'])

            self.assertEqual(np.sum(raster_gdal['BAND_G']['value']), np.sum(raster_snap['BAND_G']['value']))

    def test_mean_denoising_fail(self):
        context = Context(None)
        with self.subTest('SNAP with greater index than bands'):
            raster_snap = Read(module='snap', bands=[1, 2, 3])(self.s2_tif_path, context)
            with self.assertRaises(AssertionError):
                raster_snap = NLMeanDenoising(bands=[7])(raster_snap, context)
        with self.subTest('SNAP with wrong band name'):
            raster_snap = Read(module='snap', bands=[1, 2, 3])(self.s2_tif_path, context)
            with self.assertRaises(AssertionError):
                raster_snap = NLMeanDenoising(bands=['wrong band name'])(raster_snap, context)
