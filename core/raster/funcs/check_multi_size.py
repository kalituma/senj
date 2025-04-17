from typing import TYPE_CHECKING, Union, Optional, List
from core.util import load_snap

if TYPE_CHECKING:
    from core.raster import Raster   


def has_same_band_shape(raster: "Raster"):
    Product = load_snap("Product")

    if isinstance(raster.raw, Product):
        return not raster.raw.isMultiSize()
    else:
        return True