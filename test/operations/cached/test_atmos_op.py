import os, unittest
from core.logic import Context
from core.util import expand_var
from core.operations import Read, Write
from core.operations.cached import AtmosCorr

class TestAtmosCorr(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap',
                                        'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.wv_xml_path = os.path.join(self.data_root, 'tif', 'wv', '014493935010_01_P001_MUL',
                                        '19APR04021253-M2AS-014493935010_01_P001.XML')
        self.ps_xml_path = os.path.join(self.data_root, 'tif', 'ps', '20190817_Radiance', 'files',
                                        '20200817_013159_78_2277_3B_AnalyticMS_metadata_clip.xml')
    def test_atmos_corr_to_s2_dim(self):
        context = Context(None)
        raster = Read(module='snap')(self.s2_dim_path, context)
        raster = AtmosCorr(bands=['B1', 'B2', 'B3', 'B4', 'B5'], band_slots=['B1', 'B2', 'B3', 'B4', 'B5'],
                           write_map=True, map_dir=os.path.join(self.data_root, 'target', 'test_out', 'atmos_op'), map_stem='sentinel_map',
                           det_bnames=['B_detector_footprint_B1', 'B_detector_footprint_B2',
                                    'B_detector_footprint_B3', 'B_detector_footprint_B4',
                                    'B_detector_footprint_B5'])(raster, context)

    def test_atmos_corr_to_s2_tif(self):
        s2_tif_out = os.path.join(self.data_root, 'target', 'test_out', 'atmos_op', 'in')
        context = Context(None)
        raster = Read(module='snap')(self.s2_dim_path, context)

        out_path = Write(bands=['B2', 'B3', 'B4', 'B_detector_footprint_B2', 'B_detector_footprint_B3', 'B_detector_footprint_B4'],
                         out_ext='tif',
                         out_dir=s2_tif_out,
                         out_stem='s2_tif_snap',
                         suffix='b1_b2_b3_with_det')(raster, context)

        raster = Read(module='gdal')(out_path, context)
        AtmosCorr(bands=[1, 2, 3],
                  band_slots=['B2', 'B3', 'B4'],
                  det_bpattern='*detector*',
                  det_bword_included=True,
                  write_map=True, map_dir=os.path.join(self.data_root, 'target', 'test_out', 'atmos_op'), map_stem='sentinel_b2_to_b4_map'
                  )(raster, context)

    def test_atmos_corr_to_wv(self):
        context = Context(None)
        raster = Read(module='gdal')(self.wv_xml_path, context)
        raster = AtmosCorr(bands=['BAND_B', 'BAND_G', 'BAND_R'],
                           band_slots=['blue', 'green', 'red'],
                           write_map=True,
                           map_dir=os.path.join(self.data_root, 'target', 'test_out', 'atmos_op'),
                           map_stem='wv_map')(raster, context)
        Write(out_dir=os.path.join(self.data_root, 'target', 'test_out', 'atmos_op', 'out'),
              out_stem='014493935010_01_P001_MUL',
              suffix='atmos_corr',
              out_ext='tif')(raster, context)


    def test_atmos_corr_to_ps(self):
        context = Context(None)
        raster = Read(module='snap')(self.ps_xml_path, context)
        raster = AtmosCorr(bands=['band_1', 'band_2', 'band_3', 'band_4'],
                           band_slots=['blue', 'green', 'red', 'nir'],
                           write_map=True,
                           map_dir=os.path.join(self.data_root, 'target', 'test_out', 'atmos_op'),
                           map_stem='ps_map')(raster, context)
        Write(out_dir=os.path.join(self.data_root, 'target', 'test_out', 'atmos_op', 'out'),
              out_stem='014493935010_01_P001_MUL',
              suffix='atmos_corr',
              out_ext='tif')(raster, context)

    def test_atmos_corr_to_s2_tif_fail(self):
        context = Context(None)
        with self.subTest('the error case trying to correct sentinel2 without detector bands'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(AssertionError) as assert_error:
                AtmosCorr(bands=['B1', 'B2', 'B3', 'B4', 'B5'], band_slots=['B1', 'B2', 'B3', 'B4', 'B5'])(raster, context)
            self.assertEqual(str(assert_error.exception), 'Sentinel-2 product should have detector bands.')

        with self.subTest('the error case band_slots length short than bands length'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(AssertionError) as assert_error:
                AtmosCorr(bands=['B1', 'B2', 'B3', 'B4', 'B5'], band_slots=['B1', 'B2', 'B3', 'B4'])(raster, context)
            self.assertEqual(str(assert_error.exception), 'target_band_names and target_band_slot should have the same length')

        with self.subTest('the error case trying to correct sentinel2 with detector bands which doesnt have enough resolution cases'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(AssertionError) as assert_error:
                AtmosCorr(bands=['B2', 'B3', 'B4'], band_slots=['B2', 'B3', 'B4'],
                          det_bnames=['B_detector_footprint_B1'])(raster, context)
            self.assertEqual(str(assert_error.exception), 'Detectors should have the same resolution case number with bands. (det:0,bands:1)')

        with self.subTest('used det_bword_included, but det_bpattern is not provided'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(AssertionError) as assert_error:
                AtmosCorr(bands=['B2', 'B3', 'B4'], band_slots=['B2', 'B3', 'B4'], det_bword_included=True)(raster, context)
            self.assertEqual(str(assert_error.exception), 'det_bword should be provided when det_bword_included is True')

        with self.subTest('det_bword_included and det_bpattern is provided, but raster doesnt have any band which matches with det_bpattern'):
            raster = Read(module='snap')(self.s2_dim_path, context)
            with self.assertRaises(ValueError) as assert_error:
                AtmosCorr(bands=['B2', 'B3', 'B4'], band_slots=['B2', 'B3', 'B4'],
                          det_bword_included=True, det_bpattern='*DoesnotHave*')(raster, context)
            self.assertEqual(str(assert_error.exception), 'No matching det band found in target raster: *DoesnotHave*')