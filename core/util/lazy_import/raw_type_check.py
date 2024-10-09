from typing import TYPE_CHECKING, Union
from core.util.module_type import ModuleType
from core.util.lazy_import import import_snappy

if TYPE_CHECKING:
    from esa_snappy import Product
    from osgeo.gdal import Dataset

def is_gdal_dataset(raw:Union["Product", "Dataset"]) -> bool:
    from osgeo.gdal import Dataset
    return isinstance(raw, Dataset)

def is_snap_product(raw:Union["Product", "Dataset"]) -> bool:
    esa_snappy = import_snappy()
    return isinstance(raw, esa_snappy.Product)

def check_raw_type(raw:Union["Product", "Dataset"]) -> "ModuleType":
    if is_gdal_dataset(raw):
        return ModuleType.GDAL
    elif is_snap_product(raw):
        return ModuleType.SNAP
    else:
        raise NotImplementedError(f'raw type {type(raw)} is not implemented')
