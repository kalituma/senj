from typing import TYPE_CHECKING, Type, List, Union
from core.raster.funcs import assert_bnames, select_band_raster, get_band_name_and_index
from core.operations.parent import Op

if TYPE_CHECKING:
    from core.raster import Raster

class SelectOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def pre_process(self, raster:"Raster", selected_bands_or_indices:List[Union[str,int]], band_select:bool=False, *args, **kwargs):
        if selected_bands_or_indices:
            selected_bands, selected_indices = get_band_name_and_index(raster, selected_bands_or_indices)
            assert_bnames(selected_bands, raster.get_band_names(), f'selected bands{selected_bands} should be in source bands({raster.get_band_names()})')
            if len(selected_bands) < len(raster.get_band_names()):
                if band_select:
                    raster = select_band_raster(raster, selected_bands_or_indices)
        return raster