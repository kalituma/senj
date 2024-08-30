from cerberus import Validator

from core import OPERATIONS
from core.util import dict_with_key
from core.util.errors import check_null_error, NullValueError, ParseError
from core.config.config_validators import ConfigDependencyValidator

def get_validator(key):
    if key == 'write':
        return ConfigDependencyValidator
    else:
        return Validator

def check_root_schema(item, schema, key, allow_unknown: bool = False):
    v = ConfigDependencyValidator(schema, allow_unknown=allow_unknown)
    if not v.validate(item):
        if check_null_error(v.errors):
            raise NullValueError(key)
        else:
            raise ParseError(f'Error in {key}: {v.errors}', v.errors)

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
            if OPERATIONS.__get_attr__(op_name, 'conf_no_arg_allowed'):
                continue
            else:
                raise e