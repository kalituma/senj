import os
import unittest

from core.raster import BandError, ModuleError, ExtensionNotSupportedError
from core.operations import Read
from core.logic.context import Context


class TestReadOp(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = '../resources/data'
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_dim_path = os.path.join(self.data_root, 'dim', 's1', 'src_1', 'terrain_corrected_0.dim')
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')


        self.s1_tif_snap_path = os.path.join(self.data_root, 'tif', 's1', 'snap', 'src_1', 'terrain_corrected_0.tif')
        self.s1_tif_gdal_path = os.path.join(self.data_root, 'tif', 's1', 'gdal', 'src_1', 'terrain_corrected_0.tif')


    def test_read_snap(self):
        context = Context()
        with self.subTest('read safe file with band-word included option'):
            raster = Read(module='snap', bands=['VV'])(self.s1_safe_grdh_path, context, bname_word_included=True)
            self.assertEqual(raster.selected_bands, ['Amplitude_VV', 'Intensity_VV'])

        with self.subTest('read safe file with specified bands'):
            raster = Read(module='snap')(self.s1_safe_grdh_path, context, bname_word_included=False)
            self.assertEqual(raster.selected_bands, ['Amplitude_VV', 'Intensity_VV', 'Amplitude_VH', 'Intensity_VH'])

        with self.subTest('read s2 safe file with specified bands'):
            raster = Read(module='snap', bands=['B2', 'B4'])(self.s2_safe_path, context)
            self.assertEqual(raster.selected_bands, ['B2', 'B4'])

        with self.subTest('read s2 safe file without specified bands'):
            raster = Read(module='snap')(self.s2_safe_path, context)
            self.assertEqual(len(raster.get_band_names()), 163)

    def test_read_snap_fail(self):

        with self.subTest('wrong band name'):
            with self.assertRaises(BandError):
                Read(module='snap', bands=['VV'])(self.s1_safe_grdh_path, Context(), bname_word_included=False)

        with self.subTest('wrong module'):
            with self.assertRaises(ModuleError):
                Read(module='jpg', bands=['Sigma0_VV'])(self.s1_tif_snap_path, Context())

        with self.subTest('wrong band name'):
            with self.assertRaises(BandError):
                Read(module='snap', bands=['Delta0_VV'])(self.s1_tif_snap_path, Context())

        with self.subTest('try to read snap tif band with integer index'):
            with self.assertRaises(BandError):
                Read(module='snap', bands=[2])(self.s1_tif_snap_path, Context())

        with self.subTest('try to read gdal tif band with string name'):
            with self.assertRaises(BandError):
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