from typing import TYPE_CHECKING, List, AnyStr, Union
import numpy as np
from core.operations.parent import CachedOp

from core.registry import OPERATIONS

from core.util import percentile_norm, minmax_norm, percentile_norm_mband
from core.util.op import op_constraint, OP_Module_Type, NORMALIZE_OP
from core.raster import Raster
from core.raster.funcs import check_bname_index_valid


if TYPE_CHECKING:
    from core.logic import Context

MINMAX = 'minmax'
PERCENTILE = 'percentile'
methods = [MINMAX, PERCENTILE]

@OPERATIONS.reg(name=NORMALIZE_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Normalize(CachedOp):
    def __init__(self, method:AnyStr=MINMAX, min:float=0, max:float=255, bands:List[Union[AnyStr, int]]=None):
        super().__init__(NORMALIZE_OP)
        assert method in methods, f'method should be one of {methods}'

        self._method = method
        if method == PERCENTILE:
            assert 0 <= min <= 100 and 0 <= max <= 100, 'min and max should be in [0, 100] if method is percentile'

        self._min = min
        self._max = max

        self.selected_names_or_indices = bands

    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        if check_bname_index_valid(raster, self.selected_names_or_indices):
            selected_name_or_id = self.selected_names_or_indices
        else:
            selected_name_or_id = raster.get_band_names()

        raster = self.pre_process(raster, bands_to_load=selected_name_or_id, context=context)

        keys = []
        bands = []
        for key in raster.bands.keys():
            band = raster[key]['value'][..., np.newaxis].astype(np.float64)
            no_data = raster[key]['no_data']
            if not np.isnan(no_data):
                band[band == no_data] = np.nan
            keys.append(key)
            bands.append(band)

        bands = np.concatenate(bands, axis=2)
        if self._method == MINMAX:
            bands = (minmax_norm(bands) * 255)
            bands[np.isnan(bands)] = 0
            bands = bands.astype(np.uint8)
        elif self._method == PERCENTILE:
            bands = percentile_norm(bands, self._min, self._max)
            bands[np.isnan(bands)] = 0
            bands = (bands * 255).astype(np.uint8)

        for key, band in zip(keys, np.split(bands, len(keys), axis=2)):
            raster.bands[key]['value'] = band.squeeze()
            raster.bands[key]['no_data'] = 0

        raster = self.post_process(raster, context, clear=True)

        return raster