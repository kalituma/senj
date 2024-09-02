from functools import partial
import os
import re
from jsonpath_ng.ext import parse
from typing import Union, List, Tuple, Callable

from core import LAMBDA
from core.util import PathType, read_yaml, get_files_recursive, query_dict, assert_bnames
from core.config import LAMBDA_PATTERN, VAR_PATTERN, remove_var_bracket, remove_func_bracket, parse_sort, validate_config_func, validate_input_path, \
    validate_processor_relation

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

def replace_config_property(config, config_find_pattern, val_match_func:Callable,
                            change_val_func:Callable=lambda x:x, err_chk:Callable=None, val_func:Callable=lambda x:x):
    q_target = parse(config_find_pattern)
    for match in q_target.find(config):
        if isinstance(match.value, str) and val_match_func(match.value):
            src_value = match.value
            changed_value = change_val_func(src_value)
            if err_chk:
                err_chk(changed_value, src_value)
            match.context.value[match.path.fields[-1]] = val_func(changed_value)
        elif isinstance(match.value, list):
            matched_indices = val_match_func(match.value)
            if matched_indices is not None:
                for index in matched_indices:
                    match.value[index] = None
    return config

def replace_config_properties(config:dict) -> dict:

    def lambda_exists(changed_value, src_value):
        if not LAMBDA.__contains__(changed_value):
            raise ValueError(f'{src_value} is not a registered function')
    def get_lambda_contructor(changed_value):
        return LAMBDA.__get_attr__(name=changed_value, attr_name='constructor')

    def val_pattern_match(src_str, pattern):
        return re.match(pattern, src_str)

    # lambda
    config = replace_config_property(config, '$..func', val_match_func=partial(val_pattern_match, pattern=LAMBDA_PATTERN),
                                     change_val_func=remove_func_bracket, err_chk=lambda_exists, val_func=get_lambda_contructor)

    def band_list_none_match(target_list:list):
        none_str = 'none'
        if none_str in target_list or none_str.upper() in target_list or none_str.title() in target_list:
            return [idx for idx, row in enumerate(target_list) if row in [none_str, none_str.upper(), none_str.title()]]
        return None

    # bands_list from stack op
    config = replace_config_property(config, '$..bands_list', val_match_func=band_list_none_match)

    # meta_from from stack op
    config = replace_config_property(config, '$..meta_from', val_match_func=partial(val_pattern_match, pattern=VAR_PATTERN), change_val_func=lambda x: x.replace('{{', '').replace('}}', ''))

    return config



def parse_config(all_config:dict, schema_map:dict) -> Tuple[dict, List[str], dict, List[str], List[Tuple[str, str]], dict]:

    p_init = {}
    p_end = []
    p_link = []

    # register process nodes
    p_nodes, p_ops, n_config = extract_pnodes_pops(all_config)

    validate_processor_relation(n_config, proc_list=p_nodes)

    # replace var which represent lambda or any link used in any properties would be replaced here
    n_config = replace_config_properties(n_config)

    # loop only on top level
    for p_key, p_config in n_config.items():

        validate_config_func(p_key, p_config, schema_map)

        # write operation will be only op closing process
        if 'write' in p_config['operations']:
            p_end.append(p_key)

        input_path = p_config['input']['path']
        check_result = validate_input_path(input_path)

        for idx, (path_exist, path_type, new_path) in enumerate(check_result):
            if path_exist:
                p_config['input']['path'] = new_path
                p_init[p_key] = path_type

            if path_type == PathType.VAR:
                p_link.append((remove_var_bracket(input_path[idx]), p_key))

        # register operations using proc key
        if p_key in p_init:
            op_keys = ['input'] + p_config['operations'].copy()
            p_config['input'] = parse_sort(p_config['input'])
        else:
            op_keys = p_config['operations'].copy()

        arg_op_keys = [arg_key for arg_key in p_config if arg_key not in ['input', 'operations']]

        assert_bnames(arg_op_keys, op_keys, f'operations({op_keys}) set in config should match with operation arguments({arg_op_keys})')

        op_args = [p_config[op_key].copy() if op_key in p_config else {} for op_key in op_keys]
        p_ops[p_key] = op_dicts(op_keys, op_args)

    return n_config, p_nodes, p_init, p_end, p_link, p_ops