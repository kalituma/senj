import unittest

import core.atmos as atmos
from core.atmos.run.worldview import build_worldview_l1r
from core.atmos.run.planet import build_planet_l1r

from core.logic.context import Context
from core.operations import Read

class TestBuildL1R(unittest.TestCase):
    def setUp(self) -> None:

        self.wv_path = '/home/airs_khw/mount/expand/data/etri/1.WV-2_20190404_강릉/014493935010_01_P001_MUL/19APR04021253-M2AS_R1C1-014493935010_01_P001.TIF'
        self.ps_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/10.PlanetScope_20190403_강릉/20190403_04_Radiance/files/20190403_005542_1_0f3c_3B_AnalyticMS_clip.tif'
        self.ge_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/etri_data/4.GE-1_20190407_강릉/014493907010_01_P001_MUL/19APR07023734-M2AS_R1C1-014493907010_01_P001.TIF'

    def test_worldview_l1r(self):
        user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}
        context = Context()
        wv_raster = Read(module='gdal')(self.wv_path, context)
        build_worldview_l1r(wv_raster, meta_dict=wv_raster.meta_dict, user_settings=user_settings)

    def test_planet_l1r(self):
        user_settings = {k: atmos.settings['run'][k] for k in atmos.settings['run']}
        context = Context()
        ps_raster = Read(module='gdal')(self.ps_path, context)