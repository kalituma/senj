import os
from pathlib import Path
from core import LAMBDA

@LAMBDA.reg(name='sort_by_name')
def sort_by_name(file_name: str, pattern=None) -> str:
    return str(os.path.basename(file_name))

@LAMBDA.reg(name='sort_by_last_number')
def sort_by_last_number(file_name: str) -> int:
    return int(Path(file_name).stem.split('_')[-1])