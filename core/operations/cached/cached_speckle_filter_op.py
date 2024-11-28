from typing import TYPE_CHECKING, List, AnyStr, Union
import numpy as np
from core.operations.parent import CachedOp

from core.registry import OPERATIONS

from core.util import apply_lee_filter
from core.util.op import op_constraint, OP_Module_Type, CACHED_SPECKLE_FILTER_OP
from core.raster import Raster
from core.raster.funcs import check_bname_index_valid

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=CACHED_SPECKLE_FILTER_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class CachedSpeckleFilter(CachedOp):
    def __init__(self, bands:List[Union[AnyStr, int]]=None, drop_other_bands:bool=False):
        super().__init__(CACHED_SPECKLE_FILTER_OP)
        self.selected_names_or_indices = bands
        self.drop_other_bands = drop_other_bands

    def __call__(self, raster: Raster, context: "Context", *args, **kwargs):
        if check_bname_index_valid(raster, self.selected_names_or_indices):
            selected_name_or_id = self.selected_names_or_indices
        else:
            selected_name_or_id = raster.get_band_names()
        self.log(f"All bands are: {raster.get_band_names()}")
        self.log(f"Applying speckle filter to: {selected_name_or_id}")

        raster = self.pre_process(raster, bands_to_load=selected_name_or_id, context=context)
        raster.bands = apply_lee_filter(raster.bands, 5)
        raster = self.post_process(raster, context, clear=self.drop_other_bands)

        return raster
