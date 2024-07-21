import os
import re
from datetime import datetime


def sort_by_pattern(input: str, str_pattern:str, date_pattern:str):

    if re.search(str_pattern, input).group(0) is not None:
        return datetime.strptime(re.search(str_pattern, input).group(0), date_pattern)
    else:
        raise ValueError('No date pattern found in the input')