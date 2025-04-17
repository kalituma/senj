from typing import Optional, List, Union, TYPE_CHECKING
import numpy as np
from core import OPERATIONS

from core.util.op import op_constraint, call_constraint, OP_Module_Type, HIST_EQUAL_OP
from core.util import equalize_histogram, ProductType

from core.raster import Raster
from core.logic import Context
from core.raster.funcs import check_bname_index_valid
from core.operations.parent import CachedOp


@OPERATIONS.reg(HIST_EQUAL_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL])
class HistEqualOp(CachedOp):
    def __init__(self, bands:Optional[List[Union[str, int]]]=None):
        super().__init__(HIST_EQUAL_OP)
        self.selected_names_or_indices = bands

    @call_constraint(product_types=[ProductType.CP])
    def __call__(self, raster:Raster, context:Context, *args, **kwargs) -> Raster:
        if check_bname_index_valid(raster, self.selected_names_or_indices):
            selected_name_or_id = self.selected_names_or_indices
        else:
            selected_name_or_id = raster.get_band_names()
        
        self.log(f"Selected bands are: {selected_name_or_id}")
        raster = self.pre_process(raster, bands_to_load=selected_name_or_id, context=context)

        for bname, band in raster.bands.items():
            raster.bands[bname]['value'] = equalize_histogram(band['value']).astype(np.float32)
            self.log(f"{bname} has been hist equalized")

        raster = self.post_process(raster, context)

        return raster
