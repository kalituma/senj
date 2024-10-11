from typing import Dict, AnyStr, List
from netCDF4 import Dataset, Variable

def get_varaibles(nc_ds:Dataset) -> Dict[AnyStr, Variable]:
    if len(nc_ds.variables) > 0:
        return nc_ds.variables

    variables = {}
    if len(nc_ds.groups) > 0:
        for group in nc_ds.groups:
            if len(nc_ds.groups[group].variables) > 0:
                variables.update(nc_ds.groups[group].variables)
        return variables

    raise ValueError('No variables in the dataset')

from .nc_read import *
from .nc_meta import *
from .nc_band import *
from .nc_ds import *
from .load_nc import *