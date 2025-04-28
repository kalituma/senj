from core.vector.funcs.reader import BaseVectorReader
from core.vector.funcs import GdalVectorAdapter

from core.util import ModuleType
class ShapeGdalReader(BaseVectorReader, GdalVectorAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _init_reader(self, file_path: str):
        self.initialize(file_path, ModuleType.GDAL)

    def read(self, file_path: str, *args, **kwargs):
        self._init_reader(file_path)
        self.vector.raw = self.read_data(file_path)
        
        return self.vector
