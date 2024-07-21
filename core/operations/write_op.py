from pathlib import Path

from core import OPERATIONS
from core.operations import Op
from core.operations import WRITE_OP
from core.raster import RasterType, Raster, ModuleExtensionError, ExtensionError, EXT_MAP
from core.raster import write_raster

@OPERATIONS.reg(name=WRITE_OP)
class Write(Op):
    def __init__(self, path:str, module:str, bands:list[str]=None, out_ext:str='', prefix:str= '', suffix:str= ''):
        super().__init__(WRITE_OP)

        self._module = RasterType.from_str(module)
        self._selected_bands = bands

        self._out_ext = Path(path).suffix[1:].lower()

        if self._out_ext == '':
            if out_ext == '':
                raise ModuleExtensionError(module, EXT_MAP[module], out_ext)
            else:
                self._out_ext = out_ext
            self._is_file_specified = False
        else:
            if out_ext != '':
                if self._out_ext != out_ext:
                    raise ExtensionError(self._out_ext, out_ext)
                if self._out_ext not in EXT_MAP[module]:
                    raise ModuleExtensionError(module, EXT_MAP[module], self._out_ext)

            self._is_file_specified = True

        self._path = path
        self._prefix = f'{prefix}_' if prefix else ''
        self._suffix = f'_{suffix}' if suffix else ''

    def __call__(self, raster:Raster, *args):

        if self._selected_bands is not None:
            raster.selected_bands = self._selected_bands

        if self._suffix == '':
            suffix = raster.op_history[-1]
        else:
            suffix = self._suffix

        if self._is_file_specified:
            basename = Path(self._path).stem
            ext = self._out_ext
            output_path = str(Path(self._path).parent / f'{self._prefix}{basename}{suffix}.{ext}')
        else:
            basename = Path(raster.path).stem
            if self._out_ext:
                ext = self._out_ext
            else:
                ext = Path(raster.path).suffix
            output_path = str(Path(self._path) / f'{self._prefix}{basename}{suffix}.{ext}')

        write_raster(raster, output_path, self._module)
        raster = None
        print(f'{output_path} is saved')
        return output_path

