from core.base.adapter import BaseAdapter
from core.util.gdal import read_vector_ds

class GdalVectorAdapter(BaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def read_data(self, file_path: str, *args, **kwargs):
        return read_vector_ds(file_path)

    def write_data(self, file_path: str, *args, **kwargs):
        pass
