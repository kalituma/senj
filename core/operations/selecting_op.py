from typing import TYPE_CHECKING, List, AnyStr, Union
from core.operations.parent import SelectOp
from core.operations import OPERATIONS, SELECT_OP
from core.util import list_to_ordered_set
from core.util.op import OP_TYPE, op_constraint
from core.raster.funcs import rename_raster_bands

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic.context import Context

@OPERATIONS.reg(name=SELECT_OP, no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.GDAL, OP_TYPE.SNAP])
class Select(SelectOp):
    def __init__(self, bands:List[Union[int, AnyStr]]=None, band_labels:List[AnyStr]=None):
        super().__init__(SELECT_OP)
        self._selected_bands = bands
        self._labels = list_to_ordered_set(band_labels)

        if bands is None:
            assert band_labels is not None, 'bands or band_labels should be provided'
        if band_labels is None:
            assert bands is not None, 'bands or band_labels should be provided'

    def __call__(self, raster:"Raster", context:"Context", *args):
        if self._selected_bands:
            raster = self.pre_process(raster, selected_bands_or_indices=self._selected_bands, band_select=True)
            self._selected_bands = raster.get_band_names()

        if self._labels:
            if self._selected_bands is None:
                self._selected_bands = raster.get_band_names()

            raster = rename_raster_bands(raster, self._selected_bands, self._labels)

        raster = self.post_process(raster, context)
        return raster