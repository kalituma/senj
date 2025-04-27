from typing import List, Union, AnyStr, Optional
from pathlib import Path

from core import OPERATIONS

from core.util import expand_var
from core.util.errors import ExtensionNotSupportedError, ExtensionMatchingError, NotHaveSameBandShapeError
from core.util.op import OP_Module_Type, op_constraint, WRITE_OP
from core.operations import SelectOp

from core.raster import ModuleType, Raster, EXT_MAP
from core.raster.funcs import has_same_band_shape, check_bname_index_valid
from core.raster.funcs.writer import get_writer
DEFAULT_OUT_EXT = {
    ModuleType.GDAL : 'tif',
    ModuleType.SNAP : 'dim'
}

@OPERATIONS.reg(name=WRITE_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Write(SelectOp):
    def __init__(self, out_path: Optional[str]=None, out_dir: str = None, out_stem: str = 'out', out_ext: str = '',
                 bands: List[Union[int, AnyStr]] = None,
                 prefix: str = '', suffix: str = '', compress=False):

        super().__init__(WRITE_OP)

        if out_path is None:
            assert out_dir is not None, 'out_dir should be provided when out_path is None'

        self.selected_names_or_indices = bands
        self._setup_path_info(out_path, out_dir, out_stem, out_ext)
        self._prefix = prefix
        self._suffix = suffix
        self._compress = compress

    def _setup_path_info(self, out_path: Optional[str], out_dir: str, out_stem: str, out_ext: str) -> None:
        if out_path is not None:
            self._out_path = out_path
            self._out_dir = Path(out_path).parent
            self._out_stem = Path(out_path).stem
            self._out_ext = Path(out_path).suffix[1:]
        else:
            self._out_path = None
            self._out_dir = out_dir
            self._out_ext = out_ext
            self._out_stem = out_stem

    def __call__(self, raster:Raster, *args):

        self.log(f'Writing raster to "{self._out_dir}" with stem "{self._out_stem}" and extension "{self._out_ext}"')

        self._validate_extension(raster.module_type)
        output_path = self._build_output_path()
        selected_bands = self._get_selected_bands(raster)
        
        result = self.pre_process(raster, selected_bands_or_indices=selected_bands, band_select=True)
        
        self._validate_tif_format_for_snap(result)
        
        writer = get_writer(result)
        writer.write(output_path)

        self.post_process(result, None)
        self.log(f'Result is written to "{output_path}"')
        raster = None

        return output_path
    
    
    def _validate_extension(self, module_type: ModuleType) -> None:
        if self._out_ext == '':
            self._out_ext = DEFAULT_OUT_EXT[module_type]
        elif self._out_ext not in EXT_MAP[module_type.__str__()]:
            raise ExtensionNotSupportedError(module_type.__str__(), EXT_MAP[module_type.__str__()], self._out_ext)

    def _build_output_path(self) -> str:
        if self._out_path is not None:
            expanded_path = expand_var(self._out_path)
            Path(expanded_path).parent.mkdir(parents=True, exist_ok=True)
            return expanded_path
        else:
            expanded_dir = expand_var(self._out_dir)
            Path(expanded_dir).mkdir(parents=True, exist_ok=True)
            
            prefix_part = f"{self._prefix}_" if self._prefix else ""
            suffix_part = f"_{self._suffix}" if self._suffix else ""
            
            output_basename = f"{prefix_part}{self._out_stem}{suffix_part}.{self.counter}.{self._out_ext}"
            return f"{expanded_dir}/{output_basename}"

    def _get_selected_bands(self, raster: Raster) -> List[Union[int, AnyStr]]:
        if check_bname_index_valid(raster, self.selected_names_or_indices):
            return self.selected_names_or_indices
        return raster.get_band_names()
    
    def _validate_tif_format_for_snap(self, result: Raster) -> None:
        if self._out_ext == 'tif' and result.module_type == ModuleType.SNAP:
            if not has_same_band_shape(result):
                raster_data_list = result.raw.getRasterDataNodes()
                for i in range(raster_data_list.size()):
                    band = raster_data_list.get(i)
                    self.log(f'Band "{band.getName()}" : {band.getRasterHeight()} x {band.getRasterWidth()}', level='error')
                raise NotHaveSameBandShapeError(f'All bands should have same shape if out extensions({self._out_ext}) is for tiff format.')
    