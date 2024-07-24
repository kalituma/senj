from functools import partial
from core.util import get_files_recursive
from core.util import sort_by_pattern

def convert_dim_to_tif(root):
    str_pattern = '([12]\d{3}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])T(?:0[0-9]|1[0-9]|2[0-3])(?:[0-5][0-9])(?:[0-5][0-9]))'
    date_pattern = '%Y%m%dT%H%M%S'
    sort_func = partial(sort_by_pattern, str_pattern=str_pattern, date_pattern=date_pattern)
    dim_list = get_files_recursive(root, ['*.dim'], sort_func)


if __name__ == '__main__':
    root = '$ETRI_DATA/_sentinel_1_2/export/source/s2/'
    convert_dim_to_tif(root)