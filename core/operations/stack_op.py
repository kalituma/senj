from typing import TYPE_CHECKING, List, Union
from copy import deepcopy

from core.util import assert_bnames
from core.util.op import op_constraint, OP_Module_Type

from core.raster import ModuleType
from core.raster.funcs import get_band_name_and_index, merge_raster_func
from core.raster.funcs.converter import FormatConverter

from core.operations.parent import SelectOp
from core.operations import OPERATIONS, STACK_OP

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=STACK_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Stack(SelectOp):
    def __init__(self, bands_list:List[List[Union[str, int]]]=None, master_module:str=None, meta_from:str=None, geo_err:float=1e-5):
        super().__init__(STACK_OP)
        self._selected_bands_list = bands_list
        self._module = ModuleType.from_str(master_module)
        self._meta_from = meta_from
        self._geo_err = geo_err
        self.module_type = OP_Module_Type.from_str(master_module)

    def copy_meta(self, raster:"Raster", selected_meta:dict):

        if selected_meta is not None:
            raster.meta_dict = deepcopy(selected_meta)
            raster.copy_band_map_to_meta()
        else:
            # todo: should warn if meta_dict is not available
            pass

        return raster

    def __call__(self, rasters:List["Raster"], context:"Context", *args, **kwargs):

        assert len(rasters) > 1, 'At least two rasters are required for stacking'

        # assert self.proc_name in context.cache, f'{self.proc_name} not found in context.cache'
        if self.proc_name in context.cache:
            stack_order = context.cache[self.proc_name]['links']
            rasters.sort(key=lambda x: stack_order.index(x.raster_from))

        if self._meta_from:
            assert self._meta_from in [r.raster_from for r in rasters], f'meta_from({self._meta_from}) not found in rasters'

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
                rasters[i] = FormatConverter.convert(rasters[i], out_module=self._module)

        merged_raster = merge_raster_func(rasters, self._module, self._geo_err)

        if self._meta_from is not None:
            proc_raster_map = {r.raster_from: r for r in rasters}
            self.copy_meta(merged_raster, proc_raster_map[self._meta_from].meta_dict)

        merged_raster = self.post_process(merged_raster, context, *args, **kwargs)

        return merged_raster