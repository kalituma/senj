
from core import OPERATIONS
from core.util.op import op_constraint, OP_Module_Type
from core.operations.parent import Op
from core.operations import MULTI_WRITE_OP
from core.operations import Write, Split
from core.raster import ModuleType, Raster, EXT_MAP

@OPERATIONS.reg(name=MULTI_WRITE_OP, conf_no_arg_allowed=False)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP], must_after=Split)
class MultiWrite(Op):
    def __init__(self, out_dir:str, out_stem:str, out_ext:str=''):
        super().__init__(MULTI_WRITE_OP)
        self._out_dir = out_dir
        self._out_stem = out_stem
        self._out_ext = out_ext

    def __call__(self, rasters:list[Raster], *args) -> list[str]:
        assert len(rasters) > 0, 'No raster to write'
        assert all(rasters[0].module_type == r.module_type for r in rasters), 'All rasters must have the same module type'

        out_paths = []
        for i, raster in enumerate(rasters):
            bands_str = '_'.join([f'{b}'for b in raster.get_band_names()])
            out_path = Write(out_dir=self._out_dir, out_stem=f'{self._out_stem}.{bands_str}.{i}', out_ext=self._out_ext)(raster)
            out_paths.append(out_path)

        rasters = None
        return out_paths


