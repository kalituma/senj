from typing import TYPE_CHECKING

from core.vector import Vector
from core.util.gdal import clip_vector

if TYPE_CHECKING:
    from osgeo.ogr import Geometry

class VectorClipper:
    @staticmethod
    def clip(vector: Vector, bounds: "Geometry") -> "Vector":
        new_vector = Vector.like(vector)
        new_vector.raw = clip_vector(vector.raw, bounds, new_vector.raw)
        return new_vector