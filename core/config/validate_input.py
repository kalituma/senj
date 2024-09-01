from typing import Union, AnyStr, Tuple, List
from core.config import check_path_or_var
from core.util import PathType

def validate_input_path_recur(input_path:AnyStr) -> Tuple[bool, PathType, AnyStr]:

    # check input if it is a path or a variable
    path_exist, path_type, new_path = check_path_or_var(input_path)

    if not path_exist and (path_type == PathType.DIR or path_type == PathType.FILE):
        raise ValueError(f'{input_path} does not exist')

    return path_exist, path_type, new_path

def validate_input_path(input_path:Union[AnyStr, List[AnyStr]]) -> List[Tuple[bool, PathType, AnyStr]]:
    result = []
    if isinstance(input_path, list):
        for input_value in input_path:
            result.append(validate_input_path_recur(input_value))
    else:
        result.append(validate_input_path_recur(input_path))
    return result