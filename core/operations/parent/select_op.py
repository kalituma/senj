from typing import TYPE_CHECKING, Type, List, Union, Optional
from core.raster import ModuleType
from core.util import assert_bnames
from core.util.nc import get_band_length
from core.raster.funcs import select_band_raster, get_band_name_and_index

from core.operations.parent import Op

if TYPE_CHECKING:
    from core.raster import Raster

class SelectOp(Op):
    def __init__(self, op_name):
        super().__init__(op_name)

    def pre_process(self, raster:"Raster", selected_bands_or_indices:Optional[List[Union[str,int]]]=None, band_select:bool=False, *args, **kwargs):
        if selected_bands_or_indices:
            selected_bands, selected_indices = get_band_name_and_index(raster, selected_bands_or_indices)
            assert_bnames(selected_bands, raster.get_band_names(), f'selected bands{selected_bands} should be in source bands({raster.get_band_names()})')
            if raster.module_type == ModuleType.SNAP:
                if len(selected_bands) < raster.raw.getRasterDataNodes().size():
                    if band_select:
                        raster = select_band_raster(raster, selected_bands)
            elif raster.module_type == ModuleType.GDAL:
                if len(selected_indices) < raster.get_bands_size():
                    if band_select:
                        raster = select_band_raster(raster, selected_indices)
            elif raster.module_type == ModuleType.NETCDF:
                if len(selected_bands) < get_band_length(raster.raw):
                    if band_select:
                        raster = select_band_raster(raster, selected_bands)
        return raster