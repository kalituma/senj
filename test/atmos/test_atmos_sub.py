import os
import unittest
from datetime import datetime

from core.config import expand_var
from core.util.atmos import inputfile_test
import core.atmos as atmos

from core.atmos.setting import parse
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env

from core.util import compare_nested_dicts_with_arrays
from core.raster.gpf_module import write_metadata, read_pickle, read_gpf_bands_as_dict
from core.raster.gpf_module import find_granules_meta, read_granules_meta_from_product, \
    get_size_meta_per_band, get_reflectance_meta, get_reflectance_meta_from_product, \
    get_band_info_meta, get_band_info_meta_from_product

from core.logic.context import Context
from core.operations.read_op import Read
from core.operations.write_op import Write

class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = expand_var('$PROJECT_PATH')
        self.s2_target_path = os.path.join(self.project_path, 'data', 'test', 'target')

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

    def test_read_det(self):

        out_path = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'input')
        # s2_raster = Read(module='snap')(self.s2_safe_path, Context())
        s2_dim_raster = Read(module='snap')(self.s2_dim_path, Context())
        # size_meta = get_size_meta_per_band(s2_raster)
        Write(path=out_path, out_ext='tif', module='gdal', bands=['B1','B2','B3','B4','B5','B6',
                                                   'B_detector_footprint_B1','B_detector_footprint_B2',
                                                   'B_detector_footprint_B3','B_detector_footprint_B4',
                                                   'B_detector_footprint_B5','B_detector_footprint_B6'])(s2_dim_raster, Context())
        print()

        # read_gpf_bands_as_dict(s2_raster.raw, selected_bands=[])


    def test_build_meta(self):

        s2_raster = Read(module='snap')(self.s2_safe_path, Context())
        s2_dim_raster = Read(module='snap')(self.s2_dim_path, Context())

        with self.subTest(msg='band_size_metadata'):
            size_meta_per_band = get_size_meta_per_band(s2_raster.raw)
            size_meta_per_band_dim = get_size_meta_per_band(s2_dim_raster.raw)
            size_meta_target = read_pickle(os.path.join(self.s2_target_path, 's2', 'metadata', 'size_meta_safe.pkl'))
            self.assertNotEqual(size_meta_per_band, size_meta_per_band_dim)
            self.assertTrue(compare_nested_dicts_with_arrays(size_meta_per_band, size_meta_target))

        with self.subTest(msg='reflectance_metadata'):
            reflect_meta = get_reflectance_meta(s2_raster.meta_dict)
            product_reflect_meta = get_reflectance_meta_from_product(s2_raster.raw)
            dim_reflect_meta = get_reflectance_meta(s2_dim_raster.meta_dict)

            reflect_meta_target = read_pickle(os.path.join(self.s2_target_path, 's2', 'metadata', 'reflect_meta_safe.pkl'))

            self.assertEqual(reflect_meta, product_reflect_meta)
            self.assertEqual(reflect_meta, dim_reflect_meta)

            self.assertEqual(reflect_meta, reflect_meta_target)

        with self.subTest(msg='test metadata_scene(meta)'):
            granule_meta = find_granules_meta(s2_raster.meta_dict)
            granule_meta_product = read_granules_meta_from_product(s2_raster.raw)
            granule_dim_meta = find_granules_meta(s2_dim_raster.meta_dict)

            for key in granule_meta:
                if key == 'GRIDS':
                    continue
                self.assertTrue(compare_nested_dicts_with_arrays(granule_meta[key], granule_meta_product[key]))

            for key in granule_meta:
                self.assertTrue(compare_nested_dicts_with_arrays(granule_meta[key], granule_dim_meta[key]))

        with self.subTest(msg='test metadata_scene(band_info_metadata)'):
            band_meta = get_band_info_meta(s2_raster.meta_dict)
            product_band_meta = get_band_info_meta_from_product(s2_raster.raw)
            dim_band_meta = get_band_info_meta(s2_dim_raster.meta_dict)
            band_meta_target = read_pickle(os.path.join(self.s2_target_path, 's2', 'metadata', 'band_meta.pkl'))

            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, product_band_meta))
            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, dim_band_meta))
            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, band_meta_target))
