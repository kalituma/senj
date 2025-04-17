from typing import List, Union, TYPE_CHECKING, Callable, Optional

from core.operations.parent import CachedOp
from core import OPERATIONS, LAMBDA
from core.util import ProductType, get_callable_arg_count
from core.util.op import BAND_MATH_OP, call_constraint, OP_Module_Type, op_constraint
from core.raster.funcs import check_bname_index_valid

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=BAND_MATH_OP)
@op_constraint(avail_module_types=[OP_Module_Type.SNAP, OP_Module_Type.GDAL])
class BandMathOp(CachedOp):
    def __init__(self, func_name:str, func_target_bands:List[Union[str, int]], out_band_name:Optional[str]=None):
        super().__init__(BAND_MATH_OP)
        self.lambda_name = func_name
        self.selected_names_or_indices = func_target_bands
        self.out_band_name = out_band_name

        assert func_name in LAMBDA, f"Lambda name {func_name} is not valid"

    @call_constraint(product_types=[ProductType.S2])
    def __call__(self, raster:"Raster", context:"Context", *args, **kwargs) -> "Raster":
        if check_bname_index_valid(raster, self.selected_names_or_indices):
            selected_name_or_id = self.selected_names_or_indices
        else:
            selected_name_or_id = raster.get_band_names()
        
        self.log(f"Selected bands are: {selected_name_or_id}")
        raster = self.pre_process(raster, bands_to_load=selected_name_or_id, context=context)
        
        # get lambda function
        lambda_func:Callable = LAMBDA.__get_attr__(name=self.lambda_name, attr_name='constructor')

        # check if number of selected bands is equal to number of bands in lambda function
        assert len(selected_name_or_id) == get_callable_arg_count(lambda_func), f"Number of selected bands ({len(selected_name_or_id)}) is not equal to number of bands in lambda function ({lambda_func.func_code.co_argcount})"

        args = [raster.bands[bname]['value'] for bname in selected_name_or_id]
        out_band_value = lambda_func(*args)

        if self.out_band_name is None:
            out_band_name = self.lambda_name
        else:
            out_band_name = self.out_band_name

        # add new band to last position of raster
        raster.bands[out_band_name] = {
            'value': out_band_value,
            'no_data': raster.bands[selected_name_or_id[0]]['no_data']
        }
                
        raster = self.post_process(raster, context)
        return raster

