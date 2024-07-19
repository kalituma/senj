import os
import re
from datetime import datetime
from core import LAMBDA

@LAMBDA.reg(name='sort_by_name')
def sort_by_name(file_name: str, pattern=None) -> str:
    return str(os.path.basename(file_name))

def sort_by_pattern(input: str, str_pattern:str, date_pattern:str):

    if re.search(str_pattern, input).group(0) is not None:
        return datetime.strptime(re.search(str_pattern, input).group(0), date_pattern)
    else:
        raise ValueError('No date pattern found in the input')