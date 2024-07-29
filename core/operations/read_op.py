from typing import TYPE_CHECKING

from core import OPERATIONS

from core.operations import Op, MODULE_EXT_MAP
from core.operations import READ_OP

from core.util import check_input_ext
from core.util.errors import ExtensionNotSupportedError

from core.raster import RasterType, Raster
from core.raster import load_raster


if TYPE_CHECKING:
    from core.logic.context import Context

@OPERATIONS.reg(name=READ_OP)
class Read(Op):
    def __init__(self, module:str, bands:list=None):
        super().__init__(READ_OP)
        self._module = RasterType.from_str(module)
        self._selected_bands = bands

    def __call__(self, path:str, context:"Context", bname_word_included:bool=False, *args):

        in_ext = check_input_ext(path)

        if in_ext not in MODULE_EXT_MAP[self._module]:
            raise ExtensionNotSupportedError(self._module, MODULE_EXT_MAP[self._module], in_ext)

        result = Raster(path, self._selected_bands)
        result = load_raster(result, self._module, result.selected_bands, bname_word_included)
        result = self.post_process(result, context)

        return result