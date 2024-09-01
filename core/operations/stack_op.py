from typing import TYPE_CHECKING, List
from typing import Union

from core.util import assert_bnames

from core.util.op import op_constraint, OP_TYPE
from core.raster import merge_raster_func, RasterType
from core.raster.funcs import convert_raster, get_band_name_and_index
from core.operations.parent import SelectOp
from core.operations import OPERATIONS, STACK_OP

if TYPE_CHECKING:
    from core.raster import Raster

@OPERATIONS.reg(name=STACK_OP, conf_no_arg_allowed=True)
@op_constraint(avail_op_types=[OP_TYPE.GDAL, OP_TYPE.SNAP])
class Stack(SelectOp):
    def __init__(self, bands_list:List[List[Union[str, int]]]=None, master_module:str=None, meta_from:str=None):
        super().__init__(STACK_OP)
        self._selected_bands_list = bands_list
        self._module = RasterType.from_str(master_module)
        self._meta_from = meta_from


    def __call__(self, rasters:List["Raster"], *args, **kwargs):

        assert len(rasters) > 1, 'At least two rasters are required for stacking'

        if self._selected_bands_list:
            assert len(rasters) == len(self._selected_bands_list), 'The number of rasters and selected bands must be the same'
            for raster, co_band in zip(rasters, self._selected_bands_list):
                if co_band:
                    selected_band_name, selected_index = get_band_name_and_index(raster, co_band)
                    assert_bnames(selected_band_name, raster.get_band_names(), f'selected bands({selected_band_name}) not found in raster{raster.path}')
            co_bands = self._selected_bands_list
        else:
            co_bands = [None for _ in rasters]

        for i, (raster, selected_band) in enumerate(zip(rasters, co_bands)):
            if selected_band:
                rasters[i] = self.pre_process(raster, selected_band, band_select=True)
            if raster.module_type != self._module:
                rasters[i] = convert_raster(rasters[i], out_module=self._module)

        merged_raster = merge_raster_func(rasters, self._module)
        merged_raster = self.post_process(merged_raster, *args, **kwargs)

        return merged_raster