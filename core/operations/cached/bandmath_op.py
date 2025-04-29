from typing import List, Union, TYPE_CHECKING, Callable, Optional
import numpy as np

from core.operations.parent import CachedOp
from core import OPERATIONS, LAMBDA
from core.util import ProductType, get_callable_arg_count, percentile_norm
from core.util.op import BAND_MATH_OP, call_constraint, OP_Module_Type, op_constraint
from core.raster.funcs import check_bname_index_valid, get_band_name_and_index

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=BAND_MATH_OP)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP, OP_Module_Type.GDAL])
class BandMath(CachedOp):
    def __init__(self, func_name:str, func_target_bands:List[Union[str, int]], out_band_name:Optional[str]=None, normalize:bool=False):
        super().__init__(BAND_MATH_OP)
        self.lambda_name = func_name
        self.selected_names_or_indices = func_target_bands
        self.out_band_name = out_band_name
        self.normalize = normalize

        assert func_name in LAMBDA, f"Lambda name {func_name} is not valid"

    def __call__(self, raster:"Raster", context:"Context", *args, **kwargs) -> "Raster":
        if check_bname_index_valid(raster, self.selected_names_or_indices):
            band_name, band_index = get_band_name_and_index(raster, self.selected_names_or_indices)
        else:
            band_name = raster.get_band_names()
        
        self.log(f"BandMath operation started: {self.lambda_name}")
        self.log(f"Selected bands are: {band_name}")
        raster = self.pre_process(raster, bands_to_load=band_name, context=context)
        
        # get lambda function
        lambda_func:Callable = LAMBDA.__get_attr__(name=self.lambda_name, attr_name='constructor')

        # check if number of selected bands is equal to number of bands in lambda function
        assert len(band_name) == get_callable_arg_count(lambda_func), f"Number of selected bands ({len(band_name)}) is not equal to number of bands in lambda function ({lambda_func.func_code.co_argcount})"

        args = [raster.bands[bname]['value'] for bname in band_name]
        out_band_value = lambda_func(*args)

        if self.normalize:
            out_band_value = (percentile_norm(out_band_value, 2, 98) * 255).astype(np.int16)

        if self.out_band_name is None:
            out_band_name = self.lambda_name
        else:
            out_band_name = self.out_band_name

        # add new band to last position of raster
        raster.bands[out_band_name] = {
            'value': out_band_value,
            'no_data': raster.bands[band_name[0]]['no_data']
        }

        raster = self.post_process(raster, context, clear=False)
        return raster

