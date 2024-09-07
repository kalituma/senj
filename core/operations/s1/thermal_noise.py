from typing import TYPE_CHECKING

from core import OPERATIONS
from core.operations import ParamOp, SnappyOp, THERM_NOISE_OP

from core.util import ProductType, assert_bnames
from core.util.op import call_constraint, MODULE_TYPE, op_constraint
from core.raster import Raster, RasterType
from core.util.snap import get_polarization, thermal_noise_removal

if TYPE_CHECKING:
    from core.logic import Context

@OPERATIONS.reg(name=THERM_NOISE_OP, conf_no_arg_allowed=True)
@op_constraint(avail_module_types=[MODULE_TYPE.SNAP])
class ThermalNoiseRemoval(ParamOp, SnappyOp):
    def __init__(self, polarisations:list[str]=None):
        super().__init__(THERM_NOISE_OP)
        self. add_param(selectedPolarisations=polarisations)

    @call_constraint(module_types=[RasterType.SNAP], product_types=[ProductType.S1])
    def __call__(self, raster:Raster, context:"Context", *args, **kwargs):

        pols = get_polarization(raster.meta_dict)
        assert pols is not None, "Polarization not found in metadata"

        if not self.get_param('selectedPolarisations'):
            self.add_param(selectedPolarisations=pols)
        else:
            assert_bnames(self.get_param('selectedPolarisations'), pols, 'Selected polarizations not found in metadata')

        raster.raw = thermal_noise_removal(raster.raw, self.snap_params)
        raster = self.post_process(raster, context)
        return raster