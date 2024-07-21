import os
import unittest

from core.raster import BandError, ModuleError
from core.raster.gpf_module import load_raster_gpf
from core.operations import Read, Subset, Write
from core.logic.context import Context

class TestReadOp(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = '../resources/data'
        self.s1_safe_grdh_path = os.path.join(self.data_root, 'safe', 's1', 'S1A_IW_GRDH_1SDV_20230519T092327_20230519T092357_048601_05D86A_6D9B.SAFE')
        self.s1_safe_slc_path = os.path.join(self.data_root, 'safe', 's1', 'S1B_IW_SLC__1SDV_20190807T213153_20190807T213220_017485_020E22_1061.SAFE')
        self.s2_safe_path = os.path.join(self.data_root, 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')

    def test_read_s1_grdh(self):
        context = Context()
        read_op = Read(module='snap', bands=['VV'])
        raster = read_op(self.s1_safe_grdh_path, context, bname_word_included=True)
        self.assertEqual(raster.selected_bands, ['Amplitude_VV', 'Intensity_VV'])
        read_op = Read(module='snap')
        raster = read_op(self.s1_safe_grdh_path, context, bname_word_included=False)
        self.assertEqual(raster.selected_bands, ['Amplitude_VV', 'Intensity_VV', 'Amplitude_VH', 'Intensity_VH'])

    def test_read_s1_grdh_fail(self):
        context = Context()
        read_op = Read(module='snap', bands=['VV'])
        with self.assertRaises(BandError):
            read_op(self.s1_safe_grdh_path, context, bname_word_included=False)

    def test_read_safe_with_gdal(self):
        context = Context()
        read_op = Read(module='gdal')
        targets = [self.s1_safe_grdh_path, self.s1_safe_slc_path, self.s2_safe_path]
        for target_path in targets:
            with self.subTest(target_path=target_path):
                with self.assertRaises(ModuleError):
                    read_op(target_path, context)




