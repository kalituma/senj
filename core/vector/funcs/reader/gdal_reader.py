from core.vector.funcs.reader import BaseVectorReader
from core.vector.funcs.adapter import VectorAdapter

class ShapeGdalReader(BaseVectorReader, VectorAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def read(self, file_path: str, *args, **kwargs):
        # self.raster.read()
        pass
