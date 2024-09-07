from typing import TYPE_CHECKING, List, AnyStr, Union
from core.operations import CachedOp, NL_DENOISING_OP
from core.registry import OPERATIONS
from core.util import nonlocal_mean_denoising, assert_bnames
from core.util import percentile_norm
from core.util.op import op_constraint, MODULE_TYPE
from core.raster import Raster
from core.raster.funcs import check_bname_index_valid


if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=NL_DENOISING_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[MODULE_TYPE.GDAL, MODULE_TYPE.SNAP])
class NLMeanDenoising(CachedOp):
    def __init__(self, bands:List[Union[AnyStr, int]]=None, h:float=10, templateWindowSize:int=7, searchWindowSize:int=21):
        super().__init__(NL_DENOISING_OP)
        self.h = h
        self.templateWindowSize = templateWindowSize
        self.searchWindowSize = searchWindowSize
        self.selected_names_or_indices = bands

    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if check_bname_index_valid(raster, self.selected_names_or_indices):
            selected_name_or_id = self.selected_names_or_indices
        else:
            selected_name_or_id = raster.get_band_names()

        raster = self.pre_process(raster, bands_to_load=selected_name_or_id, context=context)

        for key in raster.bands.keys():
            raster[key]['value'] = nonlocal_mean_denoising(raster[key]['value'], h=self.h,
                                                           templateWindowSize=self.templateWindowSize, searchWindowSize=self.searchWindowSize, norm_func=percentile_norm)
        raster = self.post_process(raster, context)

        return raster