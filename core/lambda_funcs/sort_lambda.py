import os
from core import LAMBDA

@LAMBDA.reg(name='sort_by_name')
def sort_by_name(file_name: str, pattern=None) -> str:
    return str(os.path.basename(file_name))