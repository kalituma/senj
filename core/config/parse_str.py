import re, os
from functools import partial
from pathlib import Path

from core.util import PathType, sort_by_pattern, expand_var
from core.util.errors import PathNotExistsError

EXTERN_VAR_PATTERN = r'\${([^}]+)}'
PROC_VAR_PATTERN = '^{{[a-zA-Z0-9_]+}}$'
LAMBDA_PATTERN = '^!{[a-zA-Z0-9_]+}$'


def check_path_or_var(path) -> tuple[bool, PathType, str]:
    if re.match(PROC_VAR_PATTERN, path):
        return False, PathType.VAR, path

    path = expand_var(path)
    p = Path(path)
    path_type = PathType.DIR if p.is_dir() else PathType.FILE

    if p.exists():
        return True, path_type, path
    else:
        raise PathNotExistsError(path)

def remove_var_bracket(var_str):
    return var_str.replace('{{', '').replace('}}', '')

def remove_func_bracket(func_str):
    return func_str.replace('!{', '').replace('}', '')

def replace_external_vars(text:str, ext_vars:dict) -> str:
    def replace_var(match):
        var = match.group(1)
        try:
            value = ext_vars[var]
            return str(value)
        except KeyError:
            raise ValueError(f'External variable {var} is not defined')

    return re.sub(EXTERN_VAR_PATTERN, replace_var, text)

def parse_sort(atts:dict) -> dict:
    for k, att in atts.items():
        if k == 'sort':
            if 'reg_exp' in att and 'date_format' in att:
                atts['sort'] = { 'func' : partial(sort_by_pattern, str_pattern=att['reg_exp'], date_pattern=att['date_format'])}
    return atts