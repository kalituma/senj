from core.vector import Vector
from core.vector.funcs.writer import BaseVectorWriter
from core.vector.funcs import GdalVectorAdapter


class ShapeGdalWriter(BaseVectorWriter, GdalVectorAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    

    def write(self, file_path: str, vector: Vector, *args, **kwargs) -> str:
        return self.write_data(file_path, vector.raw)
        