from typing import TYPE_CHECKING

from core import OPERATIONS

from core.operations import Op, MODULE_EXT_MAP
from core.operations import READ_OP

from core.util import check_input_ext
from core.util.op import available_op, OP_TYPE
from core.util.errors import ExtensionNotSupportedError
from core.util import assert_bnames

from core.raster import RasterType, Raster
from core.raster.funcs import load_raster, select_band_raster, find_bands_contains_word

if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=READ_OP, conf_no_arg_allowed=False)
@available_op(OP_TYPE.GDAL, OP_TYPE.SNAP)
class Read(Op):
    def __init__(self, module:str, bands:list=None, bword:str='*', bname_word_included:bool=False):
        super().__init__(READ_OP)
        self._module = RasterType.from_str(module)
        self._bname_word_included = bname_word_included
        self._bword = bword
        self._selected_bands = bands

    def __call__(self, path:str, context:"Context", *args, **kwargs) -> Raster:

        if self._selected_bands:
            assert self._bname_word_included == False, "selected bands and bname_word_included cannot be used together"

        in_ext = check_input_ext(path)
        if in_ext not in MODULE_EXT_MAP[self._module]:
            raise ExtensionNotSupportedError(self._module, MODULE_EXT_MAP[self._module], in_ext)

        result = Raster(path, self._selected_bands)
        result = load_raster(result, self._module)

        if self._bname_word_included:
            assert self._bword, 'bword should be provided for bname_word_included'
            # assert self._module == RasterType.SNAP, 'bname_word_included is only available for SNAP module'
            self._selected_bands = find_bands_contains_word(result, self._bword)

        if self._selected_bands:
            assert_bnames(self._selected_bands, result.get_band_names(), f'selected bands{self._selected_bands} should be in source bands({result.get_band_names()})')
            if len(self._selected_bands) < len(result.get_band_names()):
                result = select_band_raster(result, self._selected_bands)

        result = self.post_process(result, context)

        return result