from typing import TYPE_CHECKING, Union
import functools
import warnings

if TYPE_CHECKING:
    from osgeo.gdal import Dataset

def assert_bnames(bnames:list[Union[str, int]], src_list:list[Union[str, int]], msg:str):
    assert all([bname in src_list for bname in bnames]), msg

def assert_ds_equal(datasets:list["Dataset"]):

    assert len(set([ds.GetGeoTransform() for ds in datasets])) == 1, 'The GeoTransform of the datasets must be the same'
    if datasets[0].GetProjection() != '':
        assert len(set([ds.GetProjection() for ds in datasets])) == 1, 'The Projection of the datasets must be the same'
    assert len(set([ds.RasterXSize for ds in datasets])) == 1, 'The Width of the datasets must be the same'
    assert len(set([ds.RasterYSize for ds in datasets])) == 1, 'The Height of the datasets must be the same'

def deprecated(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in future versions.",
            category=DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper
