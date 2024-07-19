from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from osgeo.gdal import Dataset

def assert_bnames(bnames:list[str], src_list:list[str], msg:str):
    assert all([bname in src_list for bname in bnames]), msg

def assert_ds_equal(datasets:list["Dataset"]):
    assert len(set([ds.GetGeoTransform() for ds in datasets])) == 1, 'The GeoTransform of the datasets must be the same'
    assert len(set([ds.GetProjection() for ds in datasets])) == 1, 'The Projection of the datasets must be the same'
    assert len(set([ds.RasterXSize for ds in datasets])) == 1, 'The Width of the datasets must be the same'
    assert len(set([ds.RasterYSize for ds in datasets])) == 1, 'The Height of the datasets must be the same'

