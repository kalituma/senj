from typing import AnyStr, TYPE_CHECKING, List, Dict
import numpy as np

from core.util import assert_bnames
from core.util.nc import get_variables, get_band_names_nc, get_target_shape, filter_variables_by_shape

if TYPE_CHECKING:
    from netCDF4 import Dataset

def get_band_length(nc_ds:"Dataset") -> int:
    target_shape = get_target_shape(nc_ds)
    filtered_variables = filter_variables_by_shape(nc_ds, target_shape)
    return len(filtered_variables)

def read_band(nc_ds: "Dataset", band_name:AnyStr):
    target_shape = get_target_shape(nc_ds)
    filtered_variables = filter_variables_by_shape(nc_ds, target_shape)

    if band_name in filtered_variables:
        return filtered_variables[band_name]
    else:
        raise ValueError(f'Band name {band_name} is not in the dataset')

def read_bands_array(nc_ds: "Dataset", selected_bands:List[AnyStr]=None):

    target_shape = get_target_shape(nc_ds)
    filtered_variables = filter_variables_by_shape(nc_ds, target_shape)

    arrs = []
    no_data_vals = []

    for name in selected_bands:
        band = filtered_variables[name]
        arrs.append(np.array(band[:]))
        no_data_vals.append(float(band._FillValue))

    return no_data_vals, arrs

def read_nc_bands_as_dict(nc_ds:"Dataset", selected_bands:List[AnyStr]=None):

    if selected_bands is None:
        selected_bands = list(get_band_names_nc(nc_ds))

    assert_bnames(selected_bands, get_band_names_nc(nc_ds), msg=f'{selected_bands} is not in {get_band_names_nc(nc_ds)}')

    nodata_vals, arr = read_bands_array(nc_ds, selected_bands)

    result = {}

    for i, name in enumerate(selected_bands):
        result[name] = {'value': arr[i], 'no_data': nodata_vals[i]}

    return result, selected_bands