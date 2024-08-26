from pathlib import Path

from core import OPERATIONS
from core.util import assert_bnames
from core.util.errors import ExtensionNotSupportedError, ExtensionMatchingError, NotHaveSameBandShapeError
from core.util.op import OP_TYPE, available_op
from core.operations import SelectOp
from core.operations import WRITE_OP
from core.raster import RasterType, Raster, EXT_MAP
from core.raster import write_raster
from core.raster.funcs import has_same_band_shape, update_cached_to_raw, select_band_raster

DEFAULT_OUT_EXT = {
    RasterType.GDAL : 'tif',
    RasterType.SNAP : 'dim'
}

@OPERATIONS.reg(name=WRITE_OP, no_arg_allowed=False)
@available_op(OP_TYPE.GDAL, OP_TYPE.SNAP)
class Write(SelectOp):
    def __init__(self, out_dir:str, out_stem:str='out', out_ext:str='', bands:list[str]=None, prefix:str= '', suffix:str= ''):
        super().__init__(WRITE_OP, bands)

        self._out_dir = out_dir
        self._out_ext = out_ext
        self._out_stem = out_stem

        self._prefix = prefix
        self._suffix = suffix

    def __call__(self, raster:Raster, *args):

        if self._out_ext == '':
            self._out_ext = DEFAULT_OUT_EXT[raster.module_type.__str__()]
        else:
            if self._out_ext not in EXT_MAP[raster.module_type.__str__()]:
                raise ExtensionNotSupportedError(raster.module_type, EXT_MAP[raster.module_type], self._out_ext)

        # if self._selected_bands is not None:
        #     raster.selected_bands = self._selected_bands

        Path(self._out_dir).mkdir(parents=True, exist_ok=True)

        output_basename = f'{f"{self._prefix}_" if self._prefix else self._prefix}{self._out_stem}{f"_{self._suffix}" if self._suffix else self._suffix}.{self._out_ext}'
        output_path = f'{self._out_dir}/{output_basename}'

        result = update_cached_to_raw(raster)  # copy bands to raw
        result = self.pre_process(result, band_select=True) # select bands first

        if self._out_ext == 'tif':
            if not has_same_band_shape(raster):
                raise NotHaveSameBandShapeError(f'All bands should have same shape if out extensions({self._out_ext}) is for tiff format.')
        write_raster(result, output_path)
        raster = None
        # print(f'{output_path} is saved')
        return output_path