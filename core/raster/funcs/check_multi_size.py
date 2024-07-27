from typing import TYPE_CHECKING
from esa_snappy import Product

if TYPE_CHECKING:
    from core.raster import Raster

def has_same_band_shape(raster: "Raster"):
    if isinstance(raster.raw, Product):
        return not raster.raw.isMultiSize()
    else:
        return True