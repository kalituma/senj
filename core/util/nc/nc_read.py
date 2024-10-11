from typing import Dict, AnyStr, List
from netCDF4 import Dataset
from pathlib import Path

from core.util.nc import get_varaibles

def read_nc(path) -> Dataset:

    ext = Path(path).suffix.lower()
    assert ext == '.nc' or ext == '.nc4', f'input file must be a tif file, but got {ext}'

    ds = Dataset(path)
    return ds

def get_band_names_nc(nc_ds:Dataset) -> List[AnyStr]:
    return list(get_varaibles(nc_ds).keys())