import os, locale, re
import numpy as np
from datetime import datetime
from pathlib import Path

from core import LAMBDA

@LAMBDA.reg(name='sort_by_name')
def sort_by_name(file_name: str, pattern=None) -> str:
    return str(os.path.basename(file_name))

@LAMBDA.reg(name='sort_by_last_number')
def sort_by_last_number(file_name: str) -> int:
    return int(Path(file_name).stem.split('_')[-1])

@LAMBDA.reg(name='sort_by_second_number')
def sort_by_second_number(file_name: str) -> int:
    return int(Path(file_name).stem.split('_')[1])

@LAMBDA.reg(name='sort_by_ge_date')
def sort_by_ge_date(file_name: str) -> datetime:
     date_paresed = re.search('(\d{2}[A-Za-z]{3}\d{2}\d{6})', Path(file_name).stem)
     if date_paresed is None:
         raise ValueError(f'Could not parse date from {file_name} to sort')
     locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
     date_obj = datetime.strptime(date_paresed.group(), '%y%b%d%H%M%S')
     return date_obj

@LAMBDA.reg(name='ndwi')
def ndwi(b2:np.ndarray, b4:np.ndarray) -> np.ndarray:
    b2 = b2.astype(np.float32)
    b4 = b4.astype(np.float32)
    return (b2 - b4) / (b2 + b4)