from core.raster.funcs import read_band_from_raw
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.raster import Raster

def load_bands(target_raster: "Raster", target_band_names:list[str], target_band_slot:list[str]) -> "Raster":

    assert len(target_band_names) == len(target_band_slot), 'Length of target_band_names and target_band_slot should be the same.'

    target_raster = read_band_from_raw(target_raster, target_band_names)

    for bname, bslot in zip(target_band_names, target_band_slot):
        target_raster[bname]['slot'] = bslot

    return target_raster