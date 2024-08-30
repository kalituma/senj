import re, os
import numpy as np
from pathlib import Path
from enum import Enum, auto

class PathType(Enum):
    FILE = auto()
    DIR = auto()
    VAR = auto()

def remove_list_elements(src_list:list[str], remove_list:list[str]) -> list[str]:
    ref_set = set(remove_list)
    return list(filter(lambda x: x not in ref_set, src_list))


def dict_with_key(key:str, value:dict) -> dict:
    return {key: value}

def check_path_or_var(path, var_pattern):
    try:
        if re.match(var_pattern, path):
            return False, PathType.VAR

        p = Path(path)
        path_type = PathType.DIR if p.is_dir() else PathType.FILE

        if p.exists():
            return True, path_type
        else:
            raise ValueError(f'{path} does not exist')
    except Exception as e:
        print(e)


def transpose_3d(arr, ch_count):
    if arr.ndim == 2:
        arr = np.expand_dims(arr, axis=0)
        return arr
    else:
        if arr.shape[0] == ch_count:
            return arr
        return np.moveaxis(arr, -1, 0)

def get_files_recursive(root: str, pattern, sort_func=None, filter_func=lambda x: x):
    p = Path(root).rglob(pattern)
    file_list = []
    for x in p:
        if x.is_file() and filter_func(str(x)):
            file_list.append(str(x))

    sorted(file_list, key=sort_func)
    # file_list = [str(x) for x in p if x.is_file() and filter_func(str(x))]
    return file_list

def check_input_ext(path):

    input_src = Path(path)
    _input_ext = input_src.suffix[1:].lower()

    exist = Path(path).exists()
    if not exist:
        raise ValueError(f'{path} does not exist')

    if _input_ext == '':
        raise ValueError('input path does not have an extension')

    if input_src.is_dir() and _input_ext != 'safe':
        raise ValueError('input path is a directory')

    return _input_ext

def expand_var(path:str) -> str:
    return os.path.expandvars(path)