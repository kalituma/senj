from typing import List, Union, AnyStr
from pathlib import Path

from core import OPERATIONS

from core.util import expand_var
from core.util.errors import ExtensionNotSupportedError, ExtensionMatchingError, NotHaveSameBandShapeError
from core.util.op import OP_Module_Type, op_constraint, WRITE_OP
from core.operations import SelectOp
from core.raster import ModuleType, Raster, EXT_MAP
from core.raster.funcs import has_same_band_shape, write_raster, check_bname_index_valid

DEFAULT_OUT_EXT = {
    ModuleType.GDAL : 'tif',
    ModuleType.SNAP : 'dim'
}

@OPERATIONS.reg(name=WRITE_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Write(SelectOp):
    def __init__(self, out_path: str=None, out_dir: str = None, out_stem: str = 'out', out_ext: str = '',
                 bands: List[Union[int, AnyStr]] = None,
                 prefix: str = '', suffix: str = '', compress=False):

        super().__init__(WRITE_OP)

        if out_path is None:
            assert out_dir is not None, 'out_dir should be provided when out_path is None'

        self.selected_names_or_indices = bands

        if out_path is not None:
            self._out_path = out_path
            self._out_dir = Path(out_path).parent
            self._out_stem = Path(out_path).stem
            self._out_ext = Path(out_path).suffix[1:]
        else:
            self._out_dir = out_dir
            self._out_ext = out_ext
            self._out_stem = out_stem

        self._prefix = prefix
        self._suffix = suffix
        self._compress = compress

    def __call__(self, raster:Raster, *args):

        self.log(f'Writing raster to "{self._out_dir}" with stem "{self._out_stem}" and extension "{self._out_ext}"')

        if self._out_ext == '':
            self._out_ext = DEFAULT_OUT_EXT[raster.module_type]
        else:
            if self._out_ext not in EXT_MAP[raster.module_type.__str__()]:
                raise ExtensionNotSupportedError(raster.module_type, EXT_MAP[raster.module_type], self._out_ext)

        # if self._selected_bands is not None:
        #     raster.selected_bands = self._selected_bands

        if self._out_path is not None:
            expanded_path = expand_var(self._out_path)
            Path(expanded_path).parent.mkdir(parents=True, exist_ok=True)
            output_path = expanded_path
        else:
            expanded_dir = expand_var(self._out_dir)
            Path(expanded_dir).mkdir(parents=True, exist_ok=True)

            output_basename = ''
            output_basename += f'{f"{self._prefix}_" if self._prefix else self._prefix}'
            output_basename += f'{self._out_stem}'
            output_basename += f'{f"_{self._suffix}" if self._suffix else self._suffix}'
            output_basename += f'.{self.counter}.{self._out_ext}'

            output_path = f'{expanded_dir}/{output_basename}'

        if check_bname_index_valid(raster, self.selected_names_or_indices):
            selected_name_or_id = self.selected_names_or_indices
        else:
            selected_name_or_id = raster.get_band_names()

        # result = update_cached_to_raw(raster)  # copy bands to raw
        result = self.pre_process(raster, selected_bands_or_indices=selected_name_or_id, band_select=True) # select bands first

        if self._out_ext == 'tif':
            if raster.module_type == ModuleType.SNAP:
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