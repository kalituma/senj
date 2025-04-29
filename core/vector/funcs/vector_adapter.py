from typing import TYPE_CHECKING

from osgeo import ogr
from core.base.adapter import BaseAdapter
from core.util.gdal import read_vector_ds, create_datasource, copy_layer, copy_features

if TYPE_CHECKING:
    from osgeo import Dataset

class GdalVectorAdapter(BaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def read_data(self, file_path: str, *args, **kwargs):
        return read_vector_ds(file_path)

    def write_data(self, file_path: str, dataset: "Dataset", *args, **kwargs):
        
        to_datasource = create_datasource(file_path)        
        copy_layer(to_datasource, dataset)
        src_layer = dataset.GetLayer()
        to_layer = to_datasource.GetLayer()
        copy_features(to_layer, src_layer)
        to_datasource.FlushCache()
        to_datasource = None
        
        return file_path

