from typing import TYPE_CHECKING, Union
from core.util import ModuleType, load_snap


if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo.gdal import Dataset

def is_gdal_dataset(raw:Union["Product", "Dataset"]) -> bool:
    from osgeo.gdal import Dataset
    return isinstance(raw, Dataset)

def is_nc_dataset(raw:Union["Product", "Dataset"]) -> bool:
    from netCDF4 import Dataset
    return isinstance(raw, Dataset)

def is_snap_product(raw:Union["Product", "Dataset"]) -> bool:
    Product = load_snap('Product')
    return isinstance(raw, Product)

def check_raw_type(raw:Union["Product", "Dataset"]) -> "ModuleType":
    if is_gdal_dataset(raw):
        return ModuleType.GDAL
    elif is_nc_dataset(raw):
        return ModuleType.NETCDF
    elif is_snap_product(raw):
        return ModuleType.SNAP
    else:
        raise NotImplementedError(f'raw type {type(raw)} is not implemented')
