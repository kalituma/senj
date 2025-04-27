from typing import TYPE_CHECKING, List
from copy import deepcopy

from core.util import assert_bnames
from core.util.op import op_constraint, OP_Module_Type

from core.raster import ModuleType

from core.raster.funcs import mosaic_raster_func
from core.raster.funcs.meta import MetaBandsManager
from core.raster.funcs.converter import FormatConverter

from core.operations.parent import SelectOp
from core.operations import OPERATIONS, MOSAIC_OP

if TYPE_CHECKING:
    from core.raster import Raster
    from core.logic import Context

@OPERATIONS.reg(name=MOSAIC_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[OP_Module_Type.GDAL, OP_Module_Type.SNAP])
class Mosaic(SelectOp):
    def __init__(self, master_module:str, bands=None):
        super().__init__(MOSAIC_OP)
        self._selected_bands = bands
        self._module = ModuleType.from_str(master_module)
        self.module_type = OP_Module_Type.from_str(master_module)

    def copy_meta(self, raster:"Raster", selected_meta:dict):

        if selected_meta is not None:
            raster.meta_dict = deepcopy(selected_meta)
            btoi = raster.get_band_names('map')
            MetaBandsManager(raster).update_band_mapping(btoi)
        else:
            # todo: should warn if meta_dict is not available
            pass

        return raster

    def __call__(self, rasters:List["Raster"], context:"Context", *args, **kwargs):

        assert len(rasters) > 1, 'At least two rasters are required for mosaic'
        assert len(set([r.product_type for r in rasters])) == 1, 'All rasters should have the same product type'
        assert len(set([len(r.get_band_names()) for r in rasters])) == 1, 'All rasters should have the same number of bands'

        assert self._module == ModuleType.GDAL, 'Mosaic operation is temporarily available for GDAL module only'

        if self._selected_bands:
            for i, raster in enumerate(rasters):
                raster[i] = self.pre_process(raster, self._selected_bands, band_select=True)

        for i, raster in enumerate(rasters):
            if raster.module_type != self._module:                
                rasters[i] = FormatConverter.convert(raster, self._module)

        mosaic_raster = mosaic_raster_func(rasters, self._module)

        # todo: update metadict with new bounds
        mosaic_raster = self.copy_meta(mosaic_raster, rasters[0].meta_dict)
        mosaic_raster = self.post_process(mosaic_raster, context)

        return mosaic_raster