
from core import OPERATIONS
from core.operations import Op
from core.operations import MULTI_WRITE_OP
from core.operations import Write
from core.raster import RasterType, Raster, EXT_MAP


@OPERATIONS.reg(name=MULTI_WRITE_OP)
class MultiWrite(Op):
    def __init__(self, path:str, module:str, out_ext:str=''):
        super().__init__(MULTI_WRITE_OP)

        self._path = path
        self._module = module
        self._out_ext = out_ext

    def __call__(self, rasters:list[Raster], *args) -> list[str]:
        assert len(rasters) > 0, 'No raster to write'

        out_paths = []
        for i, raster in enumerate(rasters):
            bands_str = '_'.join([f'{b}'for b in raster.get_band_names()])
            write_op = Write(self._path, self._module, out_ext=self._out_ext, suffix=f'{i}_{bands_str}')
            out_path = write_op(raster)
            out_paths.append(out_path)

        rasters = None
        return out_paths


