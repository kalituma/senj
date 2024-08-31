import unittest

from core import SCHEMA_PATH
from core.util import read_yaml
from core.util.errors import NullValueError, ParseError
from core.config import load_schema_map, validate_config_func


class TestParsingCerberus(unittest.TestCase):
    def setUp(self) -> None:
        self.resource_path = '../resources'
        self.schema_map = load_schema_map(SCHEMA_PATH)

        self.root_success_config = read_yaml(f'{self.resource_path}/root_success.yaml')
        self.root_fail_config = read_yaml(f'{self.resource_path}/root_fail.yaml')

    def test_parse_root_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'root' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_root_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'root' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    # success case
    def test_parse_read_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'read' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_read_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'read' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_stack_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'stack' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_stack_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'stack' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_subset_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'subset' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_subset_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'subset' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_write_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'write' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_write_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'write' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_apply_orbit_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'apply_orbit' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_apply_orbit_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'apply_orbit' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_terrain_correction_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'terrain_correction' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_terrain_correction_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'terrain_correction' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_calibrate_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'calibrate' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_calibrate_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'calibrate' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_speckle_filter_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'speckle_filter' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_speckle_filter_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'speckle_filter' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_thermal_noise_removal_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'thermal_noise_removal' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_thermal_noise_removal_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'thermal_noise_removal' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_topsar_deburst_success(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'topsar_deburst' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_topsar_deburst_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'topsar_deburst' in fail_key:
                with self.subTest():
                    with self.assertRaises(ValueError):
                        validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_convert(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'convert' in success_key:
                with self.subTest():
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_convert_fail(self):
        root_keys = list(self.root_fail_config.keys())
        for fail_key in root_keys:
            if 'convert' in fail_key:
                if fail_key == 'convert_1':
                    with self.subTest():
                        with self.assertRaises(KeyError):
                            validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)
                elif fail_key == 'convert_2':
                    with self.subTest():
                        with self.assertRaises(ValueError):
                            validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)

    def test_parse_atmos_corr(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'atmos' in success_key:
                with self.subTest(success_key):
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)

    def test_parse_atmos_corr_fail(self):
        root_keys = list(self.root_fail_config.keys())

        error_map = {
            1: {
                'error_type' : NullValueError
            },
            2: {
                'error_type' : ParseError,
                'error_msg' : "Error in atmos_corr: {'atmos_corr': [{'band_slots': ['required field'], 'bands': ['must be of list type']}]}"
            },
            3: {
                'error_type' : ParseError,
                'error_msg' : "Error in atmos_corr: {'atmos_corr': [{'band_slots': ['empty values not allowed'], 'bands': ['empty values not allowed']}]}",
            },
            4: {
                'error_type' : ParseError,
                'error_msg' : "Error in atmos_corr: {'atmos_corr': [{'write_map': ['must be of boolean type']}]}"
            },
            5: {
                'error_type': ParseError,
                'error_msg': "Error in atmos_corr: {'atmos_corr': [{'map_dir': ['value does not match regex"
            },
            6: {
                'error_type': ParseError,
                'error_msg': "Error in atmos_corr: {'atmos_corr': [{'band_slots': [\"band_slots and ['bands'] must have the same length\"]}]}"
            },
            7: {
                'error_type': ParseError,
                'error_msg': "Error in atmos_corr: {'atmos_corr': [{'map_stem': ['must be of string type']}]}"
            },
            8: {
                'error_type': ParseError,
                'error_msg': "Error in atmos_corr: {'atmos_corr': [{'det_bnames': ['empty values not allowed']}]}"
            },
            9: {
                'error_type': ParseError,
                'error_msg': "Error in atmos_corr: {'atmos_corr': [{'det_bword_included': ['must be of boolean type']}]}"
            },
            10: {
                'error_type': ParseError,
                'error_msg': "Error in atmos_corr: {'atmos_corr': [{'det_bpattern': ['must be of string type']}]}"
            }
        }

        cnt = 1
        for fail_key in root_keys:
            if 'atmos' in fail_key:
                if fail_key == f'atmos_corr_{cnt}':
                    with self.subTest(fail_key):
                        with self.assertRaises(error_map[cnt]['error_type']) as error_ctx:
                            validate_config_func(fail_key, self.root_fail_config[fail_key], self.schema_map)
                        if cnt > 1 and cnt != 5:
                            self.assertEqual(str(error_ctx.exception), str(error_map[cnt]['error_msg']))
                        elif cnt == 5:
                            self.assertTrue(error_map[cnt]['error_msg'] in str(error_ctx.exception))
                cnt += 1

    def test_parse_select(self):
        root_keys = list(self.root_success_config.keys())
        for success_key in root_keys:
            if 'select' in success_key:
                with self.subTest(success_key):
                    validate_config_func(success_key, self.root_success_config[success_key], self.schema_map)