from core.base.adapter import BaseAdapter

class GdalVectorAdapter(BaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def read_data(self, file_path: str, *args, **kwargs):
        pass

    def write_data(self, file_path: str, *args, **kwargs):
        pass
