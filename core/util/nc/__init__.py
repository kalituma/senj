from typing import Dict, AnyStr, List, Union
from netCDF4 import Dataset, Variable, Group

def get_variables(nc_ds:Union[Group, Dataset]) -> Dict[AnyStr, Variable]:

    variables = {}

    if len(nc_ds.groups) > 0:
        for group in nc_ds.groups:
            variables_dict = get_variables(nc_ds.groups[group])
            variables.update(variables_dict)

    if len(nc_ds.variables) > 0:
        root_vars = {var_name: nc_ds.variables[var_name] for var_name in nc_ds.variables}
        variables.update(root_vars)

    return variables

from .nc_read import *
from .nc_meta import *
from .nc_band import *
from .nc_ds import *
from .load_nc import *