import os
import unittest
from datetime import datetime

from core.config import expand_var
from core.util.atmos import inputfile_test
import core.atmos as atmos

from core.atmos.setting import parse
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env

from core.raster.gpf_module import read_granule_meta, get_size_meta_per_band, metadata_scene
from core.logic.context import Context
from core.operations.read_op import Read

class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = expand_var('$PROJECT_PATH')

        self.s2_safe_path = os.path.join(self.project_path, 'data', 'test', 'safe', 's2', 'S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE')
        self.s2_dim_path = os.path.join(self.project_path, 'data', 'test', 'dim', 's2', 'snap', 'subset_S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.0.dim')

        self.atmos_user_conf = os.path.join(self.project_path, 'test', 'resources', 'config', 'atmos', 'S2A_MSI.txt')

    def test_before_l1r(self):
        time_start = datetime.now()
        atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
        atmos.settings['user'] = parse(None, self.atmos_user_conf, merge=False)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
        atmos.settings['run'] = update_user_to_run(run_settings=atmos.settings['run'], user_settings=atmos.settings['user'])
        set_earthdata_login_to_env(atmos.settings['run'])
        setu = atmos.settings['run'].copy()

    def test_build_meta(self):

        s2_raster = Read(module='snap')(self.s2_safe_path, Context())
        s2_dim_raster = Read(module='snap')(self.s2_dim_path, Context())

        granule_meta = read_granule_meta(s2_raster.raw)
        size_meta_per_band = get_size_meta_per_band(s2_raster.raw)
        size_meta_per_band_2= get_size_meta_per_band(s2_dim_raster.raw)
        metadata_scene(s2_raster.raw, s2_raster.meta_dict)



