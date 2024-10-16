from typing import List, Union, AnyStr
from pathlib import Path

from core import OPERATIONS

from core.util import expand_var
from core.util.errors import ExtensionNotSupportedError, ExtensionMatchingError, NotHaveSameBandShapeError
from core.util.op import OP_Module_Type, op_constraint
from core.operations import SelectOp
from core.operations import WRITE_OP
from core.raster import ModuleType, Raster, EXT_MAP
from core.raster.funcs import has_same_band_shape, write_raster

DEFAULT_OUT_EXT = {
    ModuleType.GDAL : 'tif',
    ModuleType.SNAP : 'dim'
}

@OPERATIONS.reg(name=WRITE_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Write(SelectOp):
    def __init__(self, out_dir:str, out_stem:str='out', out_ext:str='', bands:List[Union[int,AnyStr]]=None, prefix:str= '', suffix:str= ''):
        super().__init__(WRITE_OP)

        self._selected_bands = bands
        self._out_dir = out_dir
        self._out_ext = out_ext
        self._out_stem = out_stem

        self._prefix = prefix
        self._suffix = suffix

    def __call__(self, raster:Raster, *args):

        self.log(f'Writing raster to "{self._out_dir}" with stem "{self._out_stem}" and extension "{self._out_ext}"')

        if self._out_ext == '':
            self._out_ext = DEFAULT_OUT_EXT[raster.module_type]
        else:
            if self._out_ext not in EXT_MAP[raster.module_type.__str__()]:
                raise ExtensionNotSupportedError(raster.module_type, EXT_MAP[raster.module_type], self._out_ext)

        # if self._selected_bands is not None:
        #     raster.selected_bands = self._selected_bands
        expanded_dir = expand_var(self._out_dir)
        Path(expanded_dir).mkdir(parents=True, exist_ok=True)

        output_basename = ''
        output_basename += f'{f"{self._prefix}_" if self._prefix else self._prefix}'
        output_basename += f'{self._out_stem}'
        output_basename += f'{f"_{self._suffix}" if self._suffix else self._suffix}'
        output_basename += f'.{self.counter}.{self._out_ext}'

        output_path = f'{expanded_dir}/{output_basename}'

        # result = update_cached_to_raw(raster)  # copy bands to raw
        result = self.pre_process(raster, selected_bands_or_indices=self._selected_bands, band_select=True) # select bands first

        if self._out_ext == 'tif':
            if not has_same_band_shape(result):
                raster_data_list = result.raw.getRasterDataNodes()
                for i in range(raster_data_list.size()):
                    band = raster_data_list.get(i)
                    self.log(f'Band "{band.getName()}" : {band.getRasterHeight()} x {band.getRasterWidth()}', level='error')
                raise NotHaveSameBandShapeError(f'All bands should have same shape if out extensions({self._out_ext}) is for tiff format.')
        write_raster(result, output_path)

        self.post_process(result, None)
        self.log(f'Result is written to "{output_path}"')
        raster = None

        return output_path