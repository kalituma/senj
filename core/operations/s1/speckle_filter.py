from typing import TYPE_CHECKING, Union
from core import OPERATIONS
from core.operations import SPECKLE_FILTER_OP
from core.operations import ParamOp, SnappyOp

from core.util import assert_bnames, ProductType
from core.util.op import  call_constraint, op_constraint, MODULE_TYPE

from core.raster import Raster, RasterType
from core.raster.funcs import get_band_name_and_index

from core.util.snap import SPECKLE_FILTER, FILTER_WINDOW, SIGMA_90, speckle_filter
if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=SPECKLE_FILTER_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[MODULE_TYPE.SNAP])
class SpeckleFilter(ParamOp, SnappyOp):
    def __init__(self, bands:list[Union[str,int]]=None, filter:str='LEE_SIGMA', damping_factor=2, filter_size:tuple=(3, 3), number_looks:int=1,
                 window_size:str='7x7', target_window_size:str='3x3', sigma:str=SIGMA_90, an_size=50):
        super().__init__(SPECKLE_FILTER_OP)

        self._selected_name_or_index = bands
        assert filter in [sp_filter.name for sp_filter in SPECKLE_FILTER], f"filter must be one of {SPECKLE_FILTER}"
        assert window_size in [win.value for win in FILTER_WINDOW if win.value not in ['3x3', '21x21']], f"windowSize must be one of {FILTER_WINDOW}"
        assert target_window_size in ['3x3', '5x5'], f"targetWindowSize must be one of {['3x3', '5x5']}"

        self.add_param(filter=str(SPECKLE_FILTER[filter]), dampingFactor=damping_factor, filterSizeX=filter_size[0], filterSizeY=filter_size[1],
                       numberLooksStr=str(number_looks), windowSize=window_size, targetWindowSizeStr=target_window_size, sigmaStr=str(sigma), anSize=an_size)

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):
        if self._selected_name_or_index:
            selected_bands, _ = get_band_name_and_index(raster, self._selected_name_or_index)
        else:
            selected_bands = raster.get_band_names()

        self.add_param(sourceBandNames=selected_bands)

        raster.raw = speckle_filter(raster.raw, self.snap_params)
        raster = self.post_process(raster, context)
        return raster