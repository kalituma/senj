import os
import unittest
from datetime import datetime

from core.config import expand_var
import core.atmos as atmos
from core.atmos.run import transform_l1r_meta_to_global_attrs, extract_l1r_meta, apply_atmos

from core.atmos.setting import parse
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env

from core.util import compare_nested_dicts_with_arrays
from core.raster.funcs import read_band_from_raw
from core.raster.gpf_module import write_metadata, read_pickle, read_gpf_bands_as_dict
from core.raster.gpf_module import find_grids_and_angle_meta, read_granules_meta_from_product, \
    get_size_meta_per_band_gpf, get_product_info_meta, get_reflectance_meta_from_product, \
    get_band_info_meta, get_band_info_meta_from_product

from core.raster.gdal_module import read_gdal_bands_as_dict, get_size_meta_per_band_gdal

from core.logic.context import Context
from core.operations import Read

class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = expand_var('$PROJECT_PATH')
        input_dir = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'split_safe')

        self.res_60_path = os.path.join(input_dir, 'split_safe_0_B1_B_detector_footprint_B1.tif')
        self.res_10_path = os.path.join(input_dir, 'split_safe_1_B2_B_detector_footprint_B2.tif')
        self.res_20_path = os.path.join(input_dir, 'split_safe_2_B6_B_detector_footprint_B6.tif')

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

        context = Context()
        b1_60 = Read(module='snap')(self.res_60_path, context)
        b1_60_tif = Read(module='gdal')(self.res_60_path, context)

        b2_10 = Read(module='gdal')(self.res_10_path, context)
        b3_20 = Read(module='gdal')(self.res_20_path, context)

        b1_60 = read_band_from_raw(b1_60)
        b1_60_tif = read_band_from_raw(b1_60_tif)
        b2_10 = read_band_from_raw(b2_10)
        b3_20 = read_band_from_raw(b3_20)

        with self.subTest(msg='band_size_metadata'):
            size_meta_per_band = get_size_meta_per_band_gpf(b1_60.raw)
            size_meta_per_band_gdal = get_size_meta_per_band_gdal(b1_60_tif.raw)
            print()
            # size_meta_target = read_pickle(os.path.join(self.s2_target_path, 's2', 'metadata', 'size_meta_safe.pkl'))
            # self.assertNotEqual(size_meta_per_band, size_meta_per_band_dim)
            # self.assertTrue(compare_nested_dicts_with_arrays(size_meta_per_band, size_meta_target))

        with self.subTest(msg='reflectance_metadata'):
            reflect_meta = get_product_info_meta(s2_raster.meta_dict)
            product_reflect_meta = get_reflectance_meta_from_product(s2_raster.raw)
            dim_reflect_meta = get_product_info_meta(s2_dim_raster.meta_dict)

            reflect_meta_target = read_pickle(os.path.join(self.s2_target_path, 's2', 'metadata', 'reflect_meta_safe.pkl'))

            self.assertEqual(reflect_meta, product_reflect_meta)
            self.assertEqual(reflect_meta, dim_reflect_meta)

            self.assertEqual(reflect_meta, reflect_meta_target)

        with self.subTest(msg='test metadata_scene(meta)'):
            granule_meta = find_grids_and_angle_meta(s2_raster.meta_dict)
            granule_meta_product = read_granules_meta_from_product(s2_raster.raw)
            granule_dim_meta = find_grids_and_angle_meta(s2_dim_raster.meta_dict)

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

    def test_build_l1r(self):
        input_dir = os.path.join(self.project_path, 'data', 'test', 'target', 's2', 'split_safe')
        res_60_path = os.path.join(input_dir, 'split_safe_0_B1_B_detector_footprint_B1.tif')
        res_10_path = os.path.join(input_dir, 'split_safe_1_B2_B_detector_footprint_B2.tif')
        res_20_path = os.path.join(input_dir, 'split_safe_2_B6_B_detector_footprint_B6.tif')

        context = Context()
        b1_60 = Read(module='gdal')(res_60_path, context)
        b2_10 = Read(module='gdal')(res_10_path, context)
        b3_20 = Read(module='gdal')(res_20_path, context)

        b1_60 = read_band_from_raw(b1_60)
        b2_10 = read_band_from_raw(b2_10)
        b3_20 = read_band_from_raw(b3_20)

        with self.subTest(msg='test L1R'):
            apply_atmos(b1_60, target_band_names=['B2'], target_det_names=['B_detector_footprint_B1'],
                        target_band_slot=['B2'], atmos_conf_path=self.atmos_user_conf)
            # self.assertEqual(l1r['output'], 'L1R')