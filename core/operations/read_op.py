from typing import TYPE_CHECKING, List, Union, AnyStr

from core import OPERATIONS

from core.operations import READ_OP
from core.operations.parent import SelectOp

from core.util import check_input_ext
from core.util.op import op_constraint, OP_TYPE
from core.util.errors import ExtensionNotSupportedError
from core.util import assert_bnames

from core.raster import RasterType, Raster, MODULE_EXT_MAP
from core.raster.funcs import load_raster, select_band_raster, find_bands_contains_word

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=READ_OP, conf_no_arg_allowed=False)
@op_constraint(avail_op_types=[OP_TYPE.GDAL, OP_TYPE.SNAP])
class Read(SelectOp):
    def __init__(self, module:str, bands:List[Union[int,AnyStr]]=None, bword:str='*', bname_word_included:bool=False):
        super().__init__(READ_OP)
        self._module = RasterType.from_str(module)
        self._bname_word_included = bname_word_included
        self._bword = bword
        self._selected_bands_or_indices = bands
        self.op_type = OP_TYPE.from_str(module)

    def __call__(self, path:str, context:"Context", *args, **kwargs) -> Raster:

        if self._selected_bands_or_indices:
            assert self._bname_word_included == False, "selected bands and bname_word_included cannot be used together"

        in_ext = check_input_ext(path)
        if in_ext not in MODULE_EXT_MAP[self._module.__str__()]:
            raise ExtensionNotSupportedError(self._module, MODULE_EXT_MAP[self._module.__str__()], in_ext)

        result = Raster(path)
        result = load_raster(result, self._module)

        if self._bname_word_included:
            assert self._bword, 'bword should be provided for bname_word_included'
            # assert self._module == RasterType.SNAP, 'bname_word_included is only available for SNAP module'
            self._selected_bands_or_indices = find_bands_contains_word(result, self._bword)

        result = self.pre_process(result, selected_bands_or_indices=self._selected_bands_or_indices, band_select=True) # select bands after
        result = self.post_process(result, context)

        return result