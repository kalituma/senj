import os
import unittest

from core.config import expand_var
from core.util.snap import read_gpf_bands_as_dict
from core.util.gdal import read_gdal_bands_as_dict
from core.util import ProductType, compare_nested_dicts_with_arrays
from core.util.errors import ContainedBandError, ModuleError, ExtensionNotSupportedError
from core.operations import Read, Write
from core.logic.context import Context

class TestReadOp(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = expand_var(os.path.join('$PROJECT_PATH', 'data', 'test'))

        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s2_dim_path = os.path.join(self.data_root, 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

        self.s1_tif_snap_path = os.path.join(self.data_root, 'tif', 's1', 'snap', 'src_1', 'terrain_corrected_0.tif')
        self.s2_tif_snap_path = os.path.join(self.data_root, 'tif', 's2', 'snap', 'out_0_B2_B3_B4_B_detector_footprint_B2_B_detector_footprint_B3_B_detector_footprint_B4.tif')
        self.s1_tif_gdal_path = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')
        self.s2_tif_gdal_path = os.path.join(self.data_root, 'tif', 's2', 'gdal', 'out_0_read.tif')

    def test_read_snap(self):
        context = Context()

        s2_without_meta = os.path.join(self.data_root, 's2merge_1_stack_subset.tif')

        with self.subTest('read safe file with band-word included option'):
            raster = Read(module='snap', bands=['VV'])(self.s1_safe_grdh_path, context, bname_word_included=True)
            self.assertEqual(raster.selected_bands, ['Amplitude_VV', 'Intensity_VV'])

        with self.subTest('read safe file with specified bands'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context, bname_word_included=False)
            self.assertEqual(list(raster.get_band_names()), ['Amplitude_VV', 'Intensity_VV', 'Amplitude_VH', 'Intensity_VH'])

        with self.subTest('read s2 safe file with specified bands'):
            raster = Read(module='snap', bands=['B2', 'B4'])(self.s2_safe_path, context)
            self.assertEqual(raster.selected_bands, ['B2', 'B4'])

        with self.subTest('read s2 safe file without specified bands'):
            raster = Read(module='snap')(self.s2_safe_path, context)
            self.assertEqual(len(raster.get_band_names()), 163)

        # with self.subTest('read tif using snap'):
        #     result_raster = Read(module='snap')(self.s1_tif_snap_path, context)


        with self.subTest('read tif not having meta using snap'):
            result_raster = Read(module='snap')(s2_without_meta, context)
            self.assertEqual(result_raster.meta_dict, None)
            self.assertEqual(result_raster.product_type, ProductType.UNKNOWN)

    def test_read_snap_fail(self):

        with self.subTest('wrong band name'):
            with self.assertRaises(ContainedBandError):
                Read(module='snap', bands=['VV'])(self.s1_safe_grdh_path, Context(), bname_word_included=False)

        with self.subTest('wrong module'):
            with self.assertRaises(ModuleError):
                Read(module='jpg', bands=['Sigma0_VV'])(self.s1_tif_snap_path, Context())

        with self.subTest('wrong band name'):
            with self.assertRaises(ContainedBandError):
                Read(module='snap', bands=['Delta0_VV'])(self.s1_tif_snap_path, Context())

        with self.subTest('try to read snap tif band with integer index'):
            with self.assertRaises(ContainedBandError):
                Read(module='snap', bands=[2])(self.s1_tif_snap_path, Context())

        with self.subTest('try to read gdal tif band with string name'):
            with self.assertRaises(ContainedBandError):
                Read(module='snap', bands=['Sigma0_VV'])(self.s1_tif_gdal_path, Context())

    def test_read_gdal(self):
        context = Context()
        with self.subTest('read snap tif'):
            Read(module='gdal')(self.s1_tif_snap_path, context)

        with self.subTest('read snap tif with band index'):
            Read(module='gdal', bands=[1])(self.s1_tif_snap_path, context)

        with self.subTest('read gdal tif'):
            Read(module='gdal')(self.s1_tif_gdal_path, context)

        with self.subTest('read gdal tif with band index'):
            Read(module='gdal', bands=[1])(self.s1_tif_gdal_path, context)

        with self.subTest('read tif not having meta using gdal'):
            result_raster = Read(module='gdal')(self.s2_without_meta, context)
            self.assertEqual(result_raster.meta_dict, None)
            self.assertEqual(result_raster.product_type, ProductType.UNKNOWN)


    def test_read_gdal_fail(self):
        context = Context()
        read_op = Read(module='gdal')
        targets = [self.s1_safe_grdh_path, self.s1_safe_slc_path, self.s2_safe_path, self.s1_dim_path]
        for target_path in targets:
            with self.subTest('try to open safe and dim file with gdal'):
                with self.assertRaises(ExtensionNotSupportedError):
                    read_op(target_path, context)

        with self.subTest('try to open gdal tif with string band name'):
            with self.assertRaises(AssertionError):
                Read(module='gdal', bands=['Sigma0_VV'])(self.s1_tif_gdal_path, context)

        with self.subTest('try to open snap tif with string band name'):
            with self.assertRaises(AssertionError):
                Read(module='gdal', bands=['Sigma0_VV'])(self.s1_tif_snap_path, context)

        with self.subTest('try to open tif with band name included option'):
            with self.assertRaises(AssertionError):
                Read(module='gdal', bands=[1])(self.s1_tif_snap_path, context, bname_word_included=True)

    def test_read_each_product_type(self):

        wv_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF'
        wv_meta_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS-014493935010_01_P001.XML'
        ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'
        ps_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/10.PlanetScope_20190403_강릉/20190403_04_Radiance/files/20190403_005542_1_0f3c_3B_AnalyticMS_clip.tif'

        context = Context()

        with self.subTest('read s1 and s2 safe'):
            s1_safe = Read(module='snap')(self.s1_safe_grdh_path, context)
            self.assertEqual(s1_safe.product_type, ProductType.S1)
            s1_safe_slc = Read(module='snap')(self.s1_safe_slc_path, context)
            self.assertEqual(s1_safe_slc.product_type, ProductType.S1)
            s2_safe = Read(module='snap')(self.s2_safe_path, context)
            self.assertEqual(s2_safe.product_type, ProductType.S2)

        with self.subTest('read s1 dim'):
            s1_dim = Read(module='snap')(self.s1_dim_path, context)
            self.assertEqual(s1_dim.product_type, ProductType.S1)
            s2_dim = Read(module='snap')(self.s2_dim_path, context)
            self.assertEqual(s2_dim.product_type, ProductType.S2)


        with self.subTest('read s1 tif snap'):
            s1_tif_snap = Read(module='snap')(self.s1_tif_snap_path, context)
            self.assertEqual(s1_tif_snap.product_type, ProductType.S1)
            s1_tif_gdal = Read(module='gdal')(self.s1_tif_snap_path, context)
            self.assertEqual(s1_tif_gdal.product_type, ProductType.S1)

        with self.subTest('read s2 tif snap'):
            s2_tif_snap = Read(module='snap')(self.s2_tif_snap_path, context)
            self.assertEqual(s2_tif_snap.product_type, ProductType.S2)
            s2_tif_snap = Read(module='gdal')(self.s2_tif_snap_path, context)
            self.assertEqual(s2_tif_snap.product_type, ProductType.S2)


        with self.subTest('read wv tif'):
            wv_raster = Read(module='gdal')(wv_path, context)
            self.assertEqual(wv_raster.product_type, ProductType.WV)
            self.assertEqual(wv_meta_path, wv_raster.path)
            wv_raster_snap = Read(module='snap')(wv_path, context)
            self.assertEqual(wv_raster.product_type, ProductType.WV)
            ge_raster = Read(module='gdal')(ge_path, context)
            self.assertEqual(ge_raster.product_type, ProductType.WV)


        with self.subTest('read ps tif'):
            ps_raster = Read(module='gdal')(ps_path, context)
            self.assertEqual(ps_raster.product_type, ProductType.PS)

    def test_world_view_auto_merge(self):
        context = Context()
        wv_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF'
        wv_meta_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS-014493935010_01_P001.XML'

        with self.subTest('read wv tif starting with gdal and then snap'):
            wv_raster = Read(module='gdal')(wv_path, context)
            self.assertEqual(wv_raster.product_type, ProductType.WV)
            out_path = '/home/airs_khw/mount/expand/data/etri/target/wv_mosaic/wv_mosaic_gdal.tif'
            out_path = Write(module='gdal', path=out_path)(wv_raster, context)
            out_raster = Read(module='snap')(out_path, context)

            gdal_bands, gdal_band_names = read_gdal_bands_as_dict(wv_raster.raw, band_names=wv_raster.get_band_names())
            gpf_bands, gpf_band_names = read_gpf_bands_as_dict(out_raster.raw)
            self.assertTrue(compare_nested_dicts_with_arrays(gdal_bands, gpf_bands))
            self.assertEqual(gdal_band_names, gpf_band_names)
            self.assertEqual(wv_raster.path, wv_meta_path)

        with self.subTest('read wv tif starting with snap and then gdal'):
            import numpy as np
            context = Context()

            wv_snap_raster = Read(module='snap')(wv_path, context)
            self.assertEqual(wv_snap_raster.product_type, ProductType.WV)
            out_path = '/home/airs_khw/mount/expand/data/etri/target/wv_mosaic/wv_mosaic_snap.tif'
            out_path = Write(module='snap', path=out_path)(wv_snap_raster, context)
            out_raster = Read(module='gdal')(out_path, context)

            gdal_bands, gdal_band_names = read_gdal_bands_as_dict(out_raster.raw, band_names=out_raster.get_band_names())
            gpf_bands, gpf_band_names = read_gpf_bands_as_dict(wv_snap_raster.raw)
            self.assertEqual(np.sum(gdal_bands['BAND_B']['value'] - gpf_bands['BAND_B']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['BAND_G']['value'] - gpf_bands['BAND_G']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['BAND_R']['value'] - gpf_bands['BAND_R']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['BAND_N']['value'] - gpf_bands['BAND_N']['value']), 0)
            self.assertEqual(gdal_band_names, gpf_band_names)
            self.assertEqual(wv_raster.path, wv_meta_path)

    def test_world_view_using_ge(self):
        context = Context()
        ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'
        ge_meta_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS-014493907010_01_P001.XML'

        with self.subTest('read ge tif starting with gdal and then snap'):
            ge_raster = Read(module='gdal')(ge_path, context)
            self.assertEqual(ge_raster.product_type, ProductType.WV)
            out_path = '/home/airs_khw/mount/expand/data/etri/target/ge_mosaic/ge_mosaic_gdal.tif'
            out_path = Write(module='gdal', path=out_path)(ge_raster, context)
            out_raster = Read(module='snap')(out_path, context)

            gdal_bands, gdal_band_names = read_gdal_bands_as_dict(ge_raster.raw, band_names=ge_raster.get_band_names())
            gpf_bands, gpf_band_names = read_gpf_bands_as_dict(out_raster.raw)
            self.assertTrue(compare_nested_dicts_with_arrays(gdal_bands, gpf_bands))
            self.assertEqual(gdal_band_names, gpf_band_names)
            self.assertEqual(ge_raster.path, ge_meta_path)

        with self.subTest('read ge tif starting with snap and then gdal'):
            import numpy as np
            ge_snap_raster = Read(module='snap')(ge_path, context)
            self.assertEqual(ge_snap_raster.product_type, ProductType.WV)
            out_path = '/home/airs_khw/mount/expand/data/etri/target/ge_mosaic/ge_mosaic_snap.tif'
            out_path = Write(module='snap', path=out_path)(ge_snap_raster, context)
            out_raster = Read(module='gdal')(out_path, context)

            gdal_bands, gdal_band_names = read_gdal_bands_as_dict(out_raster.raw, band_names=out_raster.get_band_names())
            gpf_bands, gpf_band_names = read_gpf_bands_as_dict(ge_snap_raster.raw)
            self.assertEqual(np.sum(gdal_bands['BAND_B']['value'] - gpf_bands['BAND_B']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['BAND_G']['value'] - gpf_bands['BAND_G']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['BAND_R']['value'] - gpf_bands['BAND_R']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['BAND_N']['value'] - gpf_bands['BAND_N']['value']), 0)
            self.assertEqual(gdal_band_names, gpf_band_names)
            self.assertEqual(ge_snap_raster.path, ge_meta_path)

    def test_planet(self):
        ps_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/10.PlanetScope_20190403_강릉/20190403_04_Radiance/files/20190403_005542_1_0f3c_3B_AnalyticMS_clip.tif'
        ps_meta_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/10.PlanetScope_20190403_강릉/20190403_04_Radiance/files/20190403_005542_1_0f3c_3B_AnalyticMS_metadata_clip.xml'
        context = Context()

        with self.subTest('read planet tif'):
            import numpy as np

            ps_raster = Read(module='gdal')(ps_path, context)
            self.assertEqual(ps_raster.product_type, ProductType.PS)
            ps_raster_snap = Read(module='snap')(ps_path, context)
            self.assertEqual(ps_raster_snap.product_type, ProductType.PS)
            self.assertEqual(ps_raster.meta_dict, ps_raster_snap.meta_dict)

            ps_meta_raster_snap = Read(module='snap')(ps_meta_path, context)
            ps_meta_raster_gdal = Read(module='gdal')(ps_meta_path, context)

            self.assertEqual(ps_raster.meta_dict, ps_meta_raster_snap.meta_dict)
            self.assertEqual(ps_raster_snap.meta_dict, ps_meta_raster_snap.meta_dict)
            self.assertEqual(ps_meta_raster_gdal.meta_dict, ps_meta_raster_snap.meta_dict)

            gdal_bands, gdal_band_names = read_gdal_bands_as_dict(ps_raster.raw, band_names=ps_raster.get_band_names())
            gdal_out_bands, gdal_out_band_names = read_gdal_bands_as_dict(ps_meta_raster_gdal.raw, band_names=ps_meta_raster_gdal.get_band_names())
            gpf_bands, gpf_band_names = read_gpf_bands_as_dict(ps_meta_raster_snap.raw)

            self.assertEqual(np.sum(gdal_bands['band_1']['value'] - gpf_bands['band_1']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['band_2']['value'] - gpf_bands['band_2']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['band_3']['value'] - gpf_bands['band_3']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['band_4']['value'] - gpf_bands['band_4']['value']), 0)

            self.assertEqual(np.sum(gdal_bands['band_1']['value'] - gdal_out_bands['band_1']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['band_2']['value'] - gdal_out_bands['band_2']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['band_3']['value'] - gdal_out_bands['band_3']['value']), 0)
            self.assertEqual(np.sum(gdal_bands['band_4']['value'] - gdal_out_bands['band_4']['value']), 0)

            self.assertEqual(gdal_band_names, gpf_band_names)
            self.assertEqual(gdal_band_names, gdal_out_band_names)

    def test_read_tif_meta(self):

        ps_file = '/home/airs_khw/mount/expand/data/etri/9.PlanetScope_20190405_고성/20190405_Radiance/files/20190404_005838_104b_3B_AnalyticMS_clip.tif'

        ctx = Context()
        gdal_raster = Read(module='gdal')(ps_file, ctx)
        snap_raster = Read(module='snap')(ps_file, ctx)
        print()

