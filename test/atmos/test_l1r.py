import os, unittest

from core.util import compare_nested_dicts_with_arrays, write_pickle
import core.atmos as atmos
from core.atmos.run.worldview import build_worldview_l1r
from core.atmos.run.planet import build_planet_l1r
from core.config import expand_var
from core.logic.context import Context
from core.operations import Read

class TestBuildL1R(unittest.TestCase):
    def setUp(self) -> None:

        self.wv_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF'
        self.ps_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/10.PlanetScope_20190403_강릉/20190403_04_Radiance/files/20190403_005542_1_0f3c_3B_AnalyticMS_clip.tif'
        self.ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'

        self.project_path = expand_var('$PROJECT_PATH')
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')
        self.l1r_dir = os.path.join(self.target_path, 's2', 'l1r_out')

    def test_worldview_l1r(self):
        user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}
        context = Context()

        wv_raster_gdal = Read(module='gdal')(self.wv_path, context)
        wv_raster_snap = Read(module='snap')(self.wv_path, context)

        # read and mosaic
        user_settings = atmos.setting.parse(wv_raster_gdal.meta_dict['sensor'], settings=user_settings)

        l1r_gdal, gattrs_gdal = build_worldview_l1r(wv_raster_gdal, target_band_names=['BAND_B', 'BAND_G', 'BAND_R', 'BAND_N'],
                                          target_band_slot=['BLUE', 'GREEN', 'RED', 'NIR1'],
                                          meta_dict=wv_raster_gdal.meta_dict, user_settings=user_settings)

        l1r_snap, gattrs_snap = build_worldview_l1r(wv_raster_snap, target_band_names=['BAND_B', 'BAND_G', 'BAND_R', 'BAND_N'],
                                          target_band_slot=['BLUE', 'GREEN', 'RED', 'NIR1'],
                                          meta_dict=wv_raster_snap.meta_dict, user_settings=user_settings)

        l1r_path = os.path.join(self.l1r_dir, 'l1r_out.wv.pkl')
        global_attrs_path = os.path.join(self.l1r_dir, 'global_attrs.wv.pkl')
        write_pickle(l1r_gdal, l1r_path)
        write_pickle(gattrs_gdal, global_attrs_path)

        self.assertTrue(compare_nested_dicts_with_arrays(l1r_gdal, l1r_snap))

    def test_ge_l1r(self):
        user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}
        context = Context()

        ge_raster_gdal = Read(module='gdal')(self.ge_path, context)
        ge_raster_snap = Read(module='snap')(self.ge_path, context)

        # read and mosaic
        user_settings = atmos.setting.parse(ge_raster_gdal.meta_dict['sensor'], settings=user_settings)

        l1r_gdal, gattrs_gdal = build_worldview_l1r(ge_raster_gdal,
                                                    target_band_names=['BAND_B', 'BAND_G', 'BAND_R', 'BAND_N'],
                                                    target_band_slot=['BLUE', 'GREEN', 'RED', 'NIR'],
                                                    meta_dict=ge_raster_gdal.meta_dict, user_settings=user_settings)

        l1r_snap, gattrs_snap = build_worldview_l1r(ge_raster_snap,
                                                    target_band_names=['BAND_B', 'BAND_G', 'BAND_R', 'BAND_N'],
                                                    target_band_slot=['BLUE', 'GREEN', 'RED', 'NIR'],
                                                    meta_dict=ge_raster_snap.meta_dict, user_settings=user_settings)

        self.assertTrue(compare_nested_dicts_with_arrays(l1r_gdal, l1r_snap))

    def test_planet_l1r(self):
        user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}

        context = Context()
        ps_raster_gdal = Read(module='gdal')(self.ps_path, context)
        ps_raster_snap = Read(module='snap')(self.ps_path, context)

        user_settings = atmos.setting.parse(ps_raster_gdal.meta_dict['sensor'], settings=user_settings)

        l1r_snap, gattrs_snap = build_planet_l1r(ps_raster_snap,
                                                 target_band_names=['band_1', 'band_2', 'band_3', 'band_4'],
                                                 target_band_slot=['BLUE', 'GREEN', 'RED', 'NIR'],
                                                 meta_dict=ps_raster_snap.meta_dict, user_settings=user_settings)

        l1r_gdal, gattrs_gdal = build_planet_l1r(ps_raster_gdal,
                                                 target_band_names=['band_1', 'band_2', 'band_3', 'band_4'],
                                                 target_band_slot=['BLUE', 'GREEN', 'RED', 'NIR'],
                                                 meta_dict=ps_raster_gdal.meta_dict, user_settings=user_settings)

        self.assertTrue(compare_nested_dicts_with_arrays(l1r_gdal, l1r_snap))
