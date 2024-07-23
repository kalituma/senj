import os
import unittest

from core.util.atmos import inputfile_test
import core.atmos as atmos
from core.atmos.run.load_settings import load_user_settings, set_l2w_and_polygon, update_user_to_run, set_earthdata_to_env

class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = '../../resources/data'
        self.resource_root = '../../resources'
        self.s2_path = '/home/airs_khw/mount/d_drive/__develope/temp/etri/senj/test/resources/data/safe/s2/S2A_MSIL1C_20230509T020651_N0509_R103_T52SDD_20230509T035526.SAFE'
        self.atmos_user_conf = '/home/airs_khw/mount/d_drive/__develope/temp/etri/senj/test/resources/config/atmos/S2A_MSI.txt'

    def test_before_l1r(self):
        from datetime import datetime
        time_start = datetime.now()
        atmos.settings['run']['runid'] = time_start.strftime('%Y%m%d_%H%M%S')
        atmos.settings['user'] = load_user_settings('S2A_MSI', self.atmos_user_conf)
        atmos.settings['user'] = set_l2w_and_polygon(atmos.settings['user'])
        atmos.settings['run'] = update_user_to_run(user_settings=atmos.settings['user'], run_settings=atmos.settings['run'])

        set_earthdata_to_env(atmos.settings['run'])
        inputfile_test(self.s2_path)
