import os
import re
from jsonpath_ng.ext import parse
from typing import Union, List, Tuple

from core import LAMBDA
from core.util import PathType, read_yaml, get_files_recursive
from core.config import LAMBDA_PATTERN, check_path_or_var, remove_var_bracket, remove_func_bracket, parse_sort, validate_config_func

def op_dicts(op_names:list, args_list:list) -> list[dict]   :
    out = list()
    for op_name, args in zip(op_names, args_list):
        op_dict = {}
        op_dict['op_name'] = op_name.lower()
        op_dict['args'] = args
        out.append(op_dict)
    return out

def load_schema_map(schema_dir:str) -> dict:

    schema_paths = get_files_recursive(schema_dir, '*.yaml')
    schema_map = dict()
    for schema_path in schema_paths:
        schema = read_yaml(schema_path)
        if len(schema) > 1:
            keys = list(schema.keys())
            for key in keys:
                if not isinstance(schema[key], dict):
                    del schema[key]
        key = list(schema.keys())[0]
        schema_map[key] = schema
    return schema_map

def extract_pnodes_pops(all_config:dict):
    p_nodes = []
    p_ops = {}
    configs = {}

    for p_key, p_config in all_config.items():
        if isinstance(p_config, dict):
            p_nodes.append(p_key)
            p_ops[p_key] = []
            configs[p_key] = p_config

    return p_nodes, p_ops, configs

def replace_lambda_var_to_func(config:dict) -> dict:

    q_target = parse('$..*')
    for match in q_target.find(config):
        if isinstance(match.value, str) and re.match(LAMBDA_PATTERN, match.value):
            # func exist
            cleaned_func_str = remove_func_bracket(match.value)
            if not LAMBDA.__contains__(cleaned_func_str):
                raise ValueError(f'{match.value} is not a registered function')

            match.context.value[match.path.fields[-1]] = LAMBDA.__get_attr__(name=cleaned_func_str, attr_name='constructor')

    return config
def validate_in_path_recur(input_path:str) -> tuple[bool, PathType]:

    # check input if it is a path or a variable
    path_exist, path_type = check_path_or_var(input_path)

    if not path_exist and (path_type == PathType.DIR or path_type == PathType.FILE):
        raise ValueError(f'{input_path} does not exist')

    return path_exist, path_type

def validate_in_path(input_path:Union[str, list[str]]) -> list[tuple[bool, PathType]]:
    result = []
    if isinstance(input_path, list):
        for input_value in input_path:
            result.append(validate_in_path_recur(input_value))
    else:
        result.append(validate_in_path_recur(input_path))
    return result

def parse_config(all_config:dict, schema_map:dict) -> Tuple[dict, List[str], dict, List[str], List[Tuple[str, str]], dict]:

    p_init = {}
    p_end = []
    p_link = []

    # register process nodes
    p_nodes, p_ops, n_config = extract_pnodes_pops(all_config)

    # loop only on top level
    for p_key, p_config in n_config.items():

        validate_config_func(p_key, p_config, schema_map)

        # when close processing
        if 'write' in p_config['operations']:
            p_end.append(p_key)

        input_path = p_config['input']['path']
        input_checks = validate_in_path(input_path)

        for idx, (path_exist, path_type) in enumerate(input_checks):
            if path_exist:
                p_init[p_key] = path_type

            if path_type == PathType.VAR:
                p_link.append((remove_var_bracket(input_path[idx]), p_key))

        # register operations using proc key
        if p_key in p_init:
            op_keys = ['input'] + p_config['operations'].copy()
            p_config['input'] = parse_sort(p_config['input'])
        else:
            op_keys = p_config['operations'].copy()

        op_args = [p_config[op_key].copy() if op_key in p_config else {} for op_key in op_keys]
        p_ops[p_key] = op_dicts(op_keys, op_args)

    # replace lambda var with function name
    n_config = replace_lambda_var_to_func(n_config)

    return n_config, p_nodes, p_init, p_end, p_link, p_ops