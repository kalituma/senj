import numpy as np
import os
import unittest
from datetime import datetime

from core.config import expand_var
import core.atmos as atmos

from core.atmos.run import transform_l1r_meta_to_global_attrs, extract_l1r_meta, apply_atmos
from core.atmos.meta import build_angles

from core.atmos.setting import parse
from core.atmos.run.load_settings import set_l2w_and_polygon, update_user_to_run, set_earthdata_login_to_env

from core.util import compare_nested_dicts_with_arrays, write_pickle, read_pickle, wkt_to_epsg

from core.raster.funcs import read_band_from_raw, get_band_grid_size

from core.raster.gpf_module import write_metadata, read_gpf_bands_as_dict
from core.raster.gpf_module import find_grids_and_angle_meta, read_grid_angle_meta_from_product, \
    get_band_grid_size_gpf, get_product_info_meta, get_reflectance_meta_from_product, \
    get_band_info_meta, get_band_info_meta_from_product

from core.raster.gdal_module import read_gdal_bands_as_dict, get_band_grid_size_gdal

from core.logic.context import Context
from core.operations import Read

class TestAtmosSubFuncs(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = expand_var('$PROJECT_PATH')
        self.target_path = os.path.join(self.project_path, 'data', 'test', 'target')
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

        with self.subTest(msg='test band_size_metadata'):
            size_meta_per_band = get_band_grid_size(b1_60)
            size_meta_per_band_gdal = get_band_grid_size(b1_60_tif)
            self.assertEqual(wkt_to_epsg(size_meta_per_band['B1']['projection']),
                             wkt_to_epsg(size_meta_per_band_gdal['B1']['projection']))
            del size_meta_per_band['B1']['projection']
            del size_meta_per_band_gdal['B1']['projection']
            self.assertEqual(size_meta_per_band_gdal['B1'], size_meta_per_band['B1'])

            size_meta_per_band_ch1 = get_band_grid_size(b1_60, selected_bands=['B1'])
            size_meta_per_band_gdal_ch1 = get_band_grid_size(b1_60_tif, selected_bands=['B1'])
            del size_meta_per_band_ch1['B1']['projection']
            del size_meta_per_band_gdal_ch1['B1']['projection']
            self.assertEqual(size_meta_per_band_ch1, size_meta_per_band_gdal_ch1)

        with self.subTest(msg='test product_info_metadata'):
            reflect_meta = get_product_info_meta(b1_60.meta_dict)
            reflect_meta_b2 = get_product_info_meta(b2_10.meta_dict)
            reflect_meta_b3 = get_product_info_meta(b3_20.meta_dict)
            product_reflect_meta = get_reflectance_meta_from_product(b1_60.raw)
            reflect_meta_target = read_pickle(os.path.join(self.target_path, 's2', 'metadata', 'reflect_meta_safe.pkl'))

            self.assertEqual(reflect_meta, product_reflect_meta)
            self.assertEqual(reflect_meta, reflect_meta_target)
            self.assertEqual(reflect_meta, reflect_meta_b2)
            self.assertEqual(reflect_meta, reflect_meta_b3)

        with self.subTest(msg='test metadata_scene(meta)'):
            grid_meta = find_grids_and_angle_meta(b1_60.meta_dict)
            grid_meta_b2 = find_grids_and_angle_meta(b2_10.meta_dict)
            grid_meta_b3 = find_grids_and_angle_meta(b3_20.meta_dict)
            grid_meta_product = read_grid_angle_meta_from_product(b1_60.raw)

            self.assertTrue(compare_nested_dicts_with_arrays(grid_meta, grid_meta_product))
            self.assertTrue(compare_nested_dicts_with_arrays(grid_meta, grid_meta_b2))
            self.assertTrue(compare_nested_dicts_with_arrays(grid_meta, grid_meta_b3))

        with self.subTest(msg='test metadata_scene(band_info_metadata)'):
            band_meta = get_band_info_meta(b1_60.meta_dict)
            band_meta_b2 = get_band_info_meta(b2_10.meta_dict)
            band_meta_b3 = get_band_info_meta(b3_20.meta_dict)
            product_band_meta = get_band_info_meta_from_product(b1_60.raw)
            band_meta_target = read_pickle(os.path.join(self.target_path, 's2', 'metadata', 'band_meta.pkl'))

            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, product_band_meta))
            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, band_meta_target))
            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, band_meta_b2))
            self.assertTrue(compare_nested_dicts_with_arrays(band_meta, band_meta_b3))

    def test_build_l1r_angle(self):
        b1_60 = Read(module='snap')(self.res_60_path, Context())
        b1_60 = read_band_from_raw(b1_60)

        selected_bands = None
        # l1r
        l1r_meta = extract_l1r_meta(b1_60, selected_band=selected_bands)

        det_size = l1r_meta['size_meta_per_band']['B_detector_footprint_B1']
        det_res = int(det_size['x_res'])

        global_attrs, user_settings = transform_l1r_meta_to_global_attrs(l1r_meta)

        band_dict = {bname: b1_60[bname] for bname in ['B1']}
        det_dict = {dname: b1_60[dname] for dname in ['B_detector_footprint_B1']}

        warp_option_for_angle = (
            global_attrs['scene_proj4_string'],
            [
                min(global_attrs['scene_xrange']), min(global_attrs['scene_yrange']),
                max(global_attrs['scene_xrange']), max(global_attrs['scene_yrange'])
            ],
            global_attrs['scene_pixel_size'][0],
            global_attrs['scene_pixel_size'][1],
            'average'  # resampling method
        )

        geometry_type = user_settings['geometry_type']

        out_angle = build_angles(selected_res=det_res, det_band=det_dict['B_detector_footprint_B1']['value'], granule_meta=l1r_meta['granule_meta'],
                                 geometry_type=geometry_type, warp_option=warp_option_for_angle,
                                 index_to_band=global_attrs['index_to_band'], proj_dict=global_attrs['proj_dict'])

        self.assertTrue(np.isclose(np.mean(out_angle['sza']), 22.649567))
        self.assertTrue(np.isclose(np.mean(out_angle['vaa']), 106.053604))
        self.assertTrue(np.isclose(np.mean(out_angle['saa']), 136.45471))
        self.assertTrue(np.isclose(np.mean(out_angle['vza']), 4.0797715))
        self.assertTrue(np.isclose(np.mean(out_angle['raa']), 44.08653))

    def test_build_l1r(self):

        context = Context()
        b1_60 = Read(module='gdal')(self.res_60_path, context)
        b2_10 = Read(module='gdal')(self.res_10_path, context)
        b3_20 = Read(module='gdal')(self.res_20_path, context)

        b1_60 = read_band_from_raw(b1_60)
        b2_10 = read_band_from_raw(b2_10)
        b3_20 = read_band_from_raw(b3_20)

        with self.subTest(msg='test L1R'):
            apply_atmos(b1_60, target_band_names=['B1'], target_det_name='B_detector_footprint_B1',
                        target_band_slot=['B1'], atmos_conf_path=self.atmos_user_conf)
            # self.assertEqual(l1r['output'], 'L1R')
