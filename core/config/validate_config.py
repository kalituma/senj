from cerberus import Validator

from core.util import dict_with_key
from core.util.errors import check_null_error, NullValueError
from core.raster import RasterType
from core.config import check_op_type, OP_TYPE
from core.operations import MODULE_EXT_MAP

class WriteValidator(Validator):
    def _validate_dependencies(self, dependencies, field, value):
        for dependency in dependencies:
            if dependency in self.document:
                dependent_value = self.document[dependency]
                if field == 'path':
                    self._check_path(field, dependency, value, dependent_value)
                elif field == 'ext':
                    self._check_ext(field, dependency, value, dependent_value)

    def _check_ext(self, field, dependency, value, dependent_value):
        out_raster_type = RasterType.from_str(dependent_value)
        if not value in MODULE_EXT_MAP[out_raster_type]:
            raise ValueError(f'"{value}" is not supported for {out_raster_type}')

    def _check_path(self, field, dependency, value, dependent_value):
        if not self._is_list(value, dependent_value):
            self._error(field, f'{dependency} must be a list')

        if self._is_list(value, dependent_value):
            if not self._have_same_len(value, dependent_value):
                self._error(field, f'{field} and {dependency} must have the same length')

        if self._is_str(value, dependent_value):
            self._error(field, f'{dependency} must be a string')
    def _is_str(self, val:str, dep_val:str):
        return isinstance(val, str) and isinstance(dep_val, str)
    def _is_list(self, val:list, dep_val:list):
        return isinstance(val, list) and isinstance(dep_val, list)

    def _have_same_len(self, val:list, dep_val:list):
        return len(val) == len(dep_val)

def get_validator(key):
    if key == 'write':
        return WriteValidator
    else:
        return Validator

def check_root_schema(item, schema, key, allow_unknown: bool = False):
    v = get_validator(key)(schema, allow_unknown=allow_unknown)
    if not v.validate(item):
        if check_null_error(v.errors):
            raise NullValueError(key)
        else:
            raise ValueError(f'Error in {key}: {v.errors}')

def validate_config_func(p_key:str, root_config:dict, schema_map:dict, allow_unknown=False):
    root_config_dict = dict_with_key('root', root_config)
    check_root_schema(root_config_dict, schema_map['root'], key=p_key, allow_unknown=True)

    ops = root_config['operations']
    for op_name in ops:
        assert op_name in schema_map, f'{op_name} is not implemented in schema'
        try:
            op_config_dict = dict_with_key(op_name, root_config[op_name])
            check_root_schema(op_config_dict, schema_map[op_name], key=op_name, allow_unknown=allow_unknown)
        except (KeyError, NullValueError) as e:
            if check_op_type(op_name) == OP_TYPE.S1:
                continue
            else:
                raise e