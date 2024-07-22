from pathlib import Path
import re
from datetime import datetime

def sort_by_pattern(input: Path, str_pattern:str, date_pattern:str) -> datetime:
    stem = input.stem
    if re.search(str_pattern, stem).group(0) is not None:
        return datetime.strptime(re.search(str_pattern, stem).group(0), date_pattern)
    else:
        raise ValueError('No date pattern found in the input')