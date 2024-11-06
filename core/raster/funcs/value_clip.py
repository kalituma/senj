from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from core.raster import Raster

def clip_value(raster:"Raster", min_val:float, max_val:float, min_clip_val:float, max_clip_val:float):
    assert raster.is_band_cached, "Clip value operation is only available for cached raster"

    for key in raster.bands:
        band = raster.bands[key]['value']
        band[band < min_val] = min_clip_val
        band[band > max_val] = max_clip_val
        raster.bands[key]['value'] = band

    return raster