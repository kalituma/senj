from typing import TYPE_CHECKING

if TYPE_CHECKING:
        from netCDF4 import Dataset

def make_meta_dict_from_nc_ds(ds:"Dataset") -> dict:
    meta_dict = {}
    for key, value in vars(ds).items():
        meta_dict[key] = value

    return meta_dict