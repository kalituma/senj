from cerberus import Validator

from core.util import dict_with_key
from core.config import check_op_type, OP_TYPE, check_null_error, NullValueError

class WriteValidator(Validator):
    def _validate_dependencies(self, dependencies, field, value):
        for dependency in dependencies:
            if dependency in self.document:
                dependent_value = self.document[dependency]
                if isinstance(value, list) and not isinstance(dependent_value, list):
                    self._error(field, f'{dependency} must be a list')

                if isinstance(value, list) and isinstance(dependent_value, list):
                    if len(value) != len(dependent_value):
                        self._error(field, f'{field} and {dependency} must have the same length')

                if isinstance(value, str) and not isinstance(dependent_value, str):
                    self._error(field, f'{dependency} must be a string')

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