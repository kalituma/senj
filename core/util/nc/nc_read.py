from typing import Dict, AnyStr, List
from netCDF4 import Dataset
from pathlib import Path

from core.util.nc import get_variables

def filter_variables_by_shape(nc_ds, target_shape=None):

    from collections import Counter
    import numpy as np
    
    variables = get_variables(nc_ds)
        
    if not variables:
        return {}
        
    var_shapes = {key: var.shape for key, var in variables.items()}
    
    if target_shape is None:
        shape_counter = Counter(var_shapes.values())
        target_shape = shape_counter.most_common(1)[0][0]            
    
    filtered_variables = {key: variables[key] for key, shape in var_shapes.items() 
                         if shape == target_shape}
    
    return filtered_variables

def get_target_shape(nc_ds):
    dimensions = getattr(nc_ds, 'dimensions', None)

    if dimensions is None:
        return None

    dims = []
    for key, value in dimensions.items():
        dim = getattr(value, 'size', None)
        if dim is not None:
            dims.append(dim)

    if len(dims) == 0:
        return None

    return tuple(dims)

def read_nc(path) -> Dataset:

    ext = Path(path).suffix.lower()
    assert ext == '.nc' or ext == '.nc4', f'input file must be a tif file, but got {ext}'

    nc_ds = Dataset(path)
    return nc_ds

def get_band_names_nc(nc_ds:Dataset) -> List[AnyStr]:

    target_shape = get_target_shape(nc_ds)
    filtered_variables = filter_variables_by_shape(nc_ds, target_shape)
    return list(filtered_variables.keys())