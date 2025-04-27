import numpy as np
from typing import TYPE_CHECKING, List, Union, AnyStr, Optional

from core import OPERATIONS
from core.operations.parent import SelectOp


from core.util import check_input_ext
from core.util.op import op_constraint, OP_Module_Type, READ_OP
from core.util.errors import ExtensionNotSupportedError
from core.util import assert_bnames

from core.raster import ModuleType, Raster, MODULE_EXT_MAP
from core.raster.funcs import find_bands_contains_word
from core.raster.funcs.reader import ReaderFactory, SafeGdalReader

if TYPE_CHECKING:
    from core.logic.context import Context


@OPERATIONS.reg(name=READ_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP, OP_Module_Type.NETCDF])
class Read(SelectOp):
    def __init__(self, module:str, bands:List[Union[int,AnyStr]]=None, *args, **kwargs):
        super().__init__(READ_OP)
        self._module = ModuleType.from_str(module)        

        self._selected_bands_or_indices = bands

        self._bname_word_included = kwargs.get('bname_word_included', False)
        self._sel_by_bword = kwargs.get('sel_by_bword', '*')
        self._stack_files = kwargs.get('stack_files', None)
        self._read_and_stack = kwargs.get('read_and_stack', False)        

        self.module_type = OP_Module_Type.from_str(module)

    def __call__(self, path:str, context:"Context", *args, **kwargs) -> Raster:

        if self._selected_bands_or_indices:
            assert self._bname_word_included == False, "selected bands and bname_word_included cannot be used together"

        in_ext = check_input_ext(path)
        if in_ext not in MODULE_EXT_MAP[self._module.__str__()]:
            raise ExtensionNotSupportedError(self._module, MODULE_EXT_MAP[self._module.__str__()], in_ext)

        reader = ReaderFactory.get_reader(path, self._module)
        if isinstance(reader, SafeGdalReader):
            assert self._stack_files is not None, 'stack_files should be provided for SafeGdalReader'
            assert self._read_and_stack == True, 'read_and_stack option should be True for SafeGdalReader'

            raster = reader.read(contained_words=self._stack_files)
        else:
            raster = reader.read()

        if self._bname_word_included:
            assert self._sel_by_bword, 'bword should be provided for bname_word_included'
            # assert self._module == RasterType.SNAP, 'bname_word_included is only available for SNAP module'
            self._selected_bands_or_indices = find_bands_contains_word(raster, self._sel_by_bword)

        raster = self.pre_process(raster, selected_bands_or_indices=self._selected_bands_or_indices, band_select=True) # select bands after
        raster = self.post_process(raster, context)

        return raster