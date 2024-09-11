from typing import TYPE_CHECKING, List, Union
from copy import deepcopy

from core.util import assert_bnames
from core.util.op import op_constraint, MODULE_TYPE

from core.raster import RasterType

from core.raster.funcs import convert_raster, mosaic_raster_func

from core.operations.parent import SelectOp
from core.operations import OPERATIONS, MOSAIC_OP

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=MOSAIC_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[MODULE_TYPE.GDAL, MODULE_TYPE.SNAP])
class Mosaic(SelectOp):
    def __init__(self, master_module:str, bands=None):
        super().__init__(MOSAIC_OP)
        self._selected_bands = bands
        self._module = RasterType.from_str(master_module)
        self.module_type = MODULE_TYPE.from_str(master_module)

    def copy_meta(self, raster:"Raster", selected_meta:dict):

        if selected_meta is not None:
            raster.meta_dict = deepcopy(selected_meta)
            raster.copy_band_map_to_meta()
        else:
            # todo: should warn if meta_dict is not available
            pass

        return raster

    def __call__(self, rasters:List["Raster"], context:"Context", *args, **kwargs):

        assert len(rasters) > 1, 'At least two rasters are required for mosaic'
        assert len(set([r.product_type for r in rasters])) == 1, 'All rasters should have the same product type'
        assert len(set([len(r.get_band_names()) for r in rasters])) == 1, 'All rasters should have the same number of bands'

        assert self._module == RasterType.GDAL, 'Mosaic operation is temporarily available for GDAL module only'

        if self._selected_bands:
            for i, raster in enumerate(rasters):
                raster[i] = self.pre_process(raster, self._selected_bands, band_select=True)

        for i, raster in enumerate(rasters):
            if raster.module_type != self._module:
                rasters[i] = convert_raster(raster, self._module)

        mosaic_raster = mosaic_raster_func(rasters, self._module)

        # todo: update metadict with new bounds
        mosaic_raster = self.copy_meta(mosaic_raster, rasters[0].meta_dict)
        mosaic_raster = self.post_process(mosaic_raster, context)

        return mosaic_raster