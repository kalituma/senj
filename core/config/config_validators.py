from enum import Enum
from cerberus import Validator
from core.raster import RasterType
from core.operations import MODULE_EXT_MAP

class ValidatorRule(Enum):
    SAME_LENGTH = 'same_length_with'
    EXT = 'ext'
    PATH = 'path'

    @staticmethod
    def from_str(s:str):
        if s == 'same_length_with':
            return ValidatorRule.SAME_LENGTH
        elif s == 'ext':
            return ValidatorRule.EXT
        elif s == 'path':
            return ValidatorRule.PATH
        else:
            raise ValueError(f'"{s}" is not supported')

class ConfigDependencyValidator(Validator):
    def _validate_dependencies(self, dependencies:dict, field, in_value):

        for rule_str, values in dependencies.items():
            rule = ValidatorRule.from_str(rule_str)
            if rule == ValidatorRule.SAME_LENGTH:
                if not self._have_same_len(in_value, dep_fields=dependencies[rule_str]):
                    self._error(field, f'{field} and {dependencies[rule_str]} must have the same length')
            else:
                raise ValueError(f'"{rule}" is not supported')

    # def _check_ext(self, field, dependency, value, dependent_value):
    #     out_raster_type = RasterType.from_str(dependent_value)
    #     if not value in MODULE_EXT_MAP[out_raster_type]:
    #         raise ValueError(f'"{value}" is not supported for {out_raster_type}')
    #
    # def _check_path(self, field, dependency, value, dependent_value):
    #     if not self._is_list(value, dependent_value):
    #         self._error(field, f'{dependency} must be a list')
    #
    #     if self._is_list(value, dependent_value):
    #         if not self._have_same_len(value, dependent_value):
    #             self._error(field, f'{field} and {dependency} must have the same length')
    #
    #     if self._is_str(value, dependent_value):
    #         self._error(field, f'{dependency} must be a string')
    #
    # def _is_str(self, val:str, dep_val:str):
    #     return isinstance(val, str) and isinstance(dep_val, str)
    # def _is_list(self, val:list, dep_val:list):
    #     return isinstance(val, list) and isinstance(dep_val, list)

    def _have_same_len(self, cur_values:list, dep_fields:list):
        for dep_field in dep_fields:
            if len(cur_values) != len(self.document[dep_field]):
                return False
        return True