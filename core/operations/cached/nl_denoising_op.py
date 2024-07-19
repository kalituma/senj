from typing import TYPE_CHECKING
from core.operations import CachedOp, NL_DENOISING_OP
from core.registry import OPERATIONS
from core.util import nonlocal_mean_denoising, assert_bnames
from core.util import percentile_norm
from core.raster import Raster

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=NL_DENOISING_OP)
class NLMeanDenoising(CachedOp):
    def __init__(self, h:float=10, templateWindowSize:int=7, searchWindowSize:int=21, bands:list[str]=None):
        super().__init__(NL_DENOISING_OP)
        self.h = h
        self.templateWindowSize = templateWindowSize
        self.searchWindowSize = searchWindowSize
        self.bands = bands

    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if self.bands:
            selected_bands = self.bands
        elif raster.selected_bands:
            selected_bands = raster.selected_bands
        else:
            selected_bands = raster.get_band_names()

        assert_bnames(selected_bands, raster.get_band_names(), f'selected bands not found in raster{raster.path}')
        raster = self.pre_process(raster, context)

        for key in raster.bands.keys():
            raster[key]['value'] = nonlocal_mean_denoising(raster[key]['value'], h=self.h, templateWindowSize=self.templateWindowSize, searchWindowSize=self.searchWindowSize,
                                                           norm_func=percentile_norm)
        raster = self.post_process(raster, context)
        return raster